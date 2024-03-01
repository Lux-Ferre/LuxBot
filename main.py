from multiprocessing import Process, Manager
from multiprocessing.queues import Queue

from idle_pixel_bot import Game
from apis import APIs
from wshandlers import WSHandlers
from customs import Customs
from chat import Chat
from repo import Repo
from fun_stuff import Fun
from mod_stuff import Mod
from admin_stuff import Admin
from stats_stuff import Stats
from event_stuff import Event
from integration_stuff import Integrations


class PrimaryHandler:
    def __init__(self, p_queue: Queue):
        self.p_q = p_queue
        self.db = Repo()
        self.main_thread = self.create_main_process()
        self.api_process = self.create_api_process()
        self.ws_handlers = WSHandlers(self.p_q)
        self.customs = Customs(self.p_q, self.db)
        self.chat = Chat(self.p_q, self.db)
        self.fun = Fun(self.p_q, self.db)
        self.mod = Mod(self.p_q, self.db)
        self.admin = Admin(self.p_q, self.db)
        self.stats = Stats(self.p_q, self.db)
        self.event = Event(self.p_q, self.db)
        self.integration = Integrations(self.p_q, self.db)

        self.ws_handlers.apply_dispatch_map()

    def dispatch(self, target: dict):
        match target["action"]:
            case "main_start":
                self.main_thread.start()
                self.api_process.start()
            case "main_close":
                self.main_thread.terminate()
            case "main_restart":
                self.main_thread.terminate()
                self.main_thread = self.create_main_process()
                self.main_thread.start()
            case _:
                pass

    def create_main_process(self) -> Process:
        return Process(target=Game(self.p_q, game_queue).run)

    def create_api_process(self) -> Process:
        return Process(target=APIs(self.p_q, api_queue).run)


if __name__ == '__main__':
    manager = Manager()
    primary_queue = manager.Queue()
    game_queue = manager.Queue()
    api_queue = manager.Queue()

    main_action = {
        "target": "main",
        "action": "main_start",
        "payload": "",
        "source": "main",
    }

    primary_handler = PrimaryHandler(primary_queue)
    primary_handler.p_q.put(main_action)

    while True:
        action = primary_queue.get()
        match action["target"]:
            case "main":
                primary_handler.dispatch(action)
            case "game":
                game_queue.put(action)
            case "api":
                api_queue.put(action)
            case "ws_handlers":
                primary_handler.ws_handlers.dispatch(action)
            case "custom":
                primary_handler.customs.handle(action)
            case "chat":
                primary_handler.chat.handle(action)
            case "fun":
                primary_handler.fun.dispatch(action)
            case "mod":
                primary_handler.mod.dispatch(action)
            case "admin":
                primary_handler.admin.dispatch(action)
            case "stats":
                primary_handler.stats.dispatch(action)
            case "event":
                primary_handler.event.dispatch(action)
            case "integration":
                primary_handler.integration.dispatch(action)
            case _:
                print(f"Invalid primary handler for: {action}")
