from multiprocessing.queues import Queue
from collections import deque

from repo import Repo
from utils import Utils


class Integrations:
    def __init__(self, p_q: Queue, db: Repo):
        self.p_q = p_q
        self.db = db
        self.dispatch_map = {
            "chat_hist_request": {
                "target": self.chat_hist_request
            },
            "log_chat_history": {
                "target": self.log_chat_history
            },
        }
        self.chat_history = deque([], 5)

    def dispatch(self, action: dict):
        target_dict = self.dispatch_map.get(action["action"], None)

        if target_dict is None:
            print(f"Integration dispatch error: No handler for {action['action']}")
            return

        target_dict["target"](action)

    def log_chat_history(self, action):
        chat_data = action["payload"]["payload"]
        self.chat_history.append(chat_data)

    def chat_hist_request(self, action: dict):
        player = action["payload"]["player"]
        perm_level = player["perm_level"]
        command = action["payload"]["command"]

        if command != "logon":
            return

        if perm_level < 0:
            return

        chat_history = self.chat_history

        actions = []

        for message in chat_history:
            reply_data = {
                "player": player["username"],
                "plugin": "chathist",
                "command": "addMessage",
                "payload": message,
            }

            send_action = Utils.gen_send_action("custom", reply_data)
            actions.append(send_action)

        reply_data = {
            "player": player["username"],
            "plugin": "chathist",
            "command": "endstream",
            "payload": "none",
        }

        send_action = Utils.gen_send_action("custom", reply_data)
        actions.append(send_action)

        for new_action in actions:
            self.p_q.put(new_action)
