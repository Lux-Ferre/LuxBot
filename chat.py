from multiprocessing.queues import Queue

from repo import Repo


class Chat:
    def __init__(self, p_q: Queue, db: Repo):
        self.dispatch_map = {
            "handle": {
                "target": self.handle,
            }
        }
        self.p_q = p_q
        self.db = db

    def dispatch(self, action: dict):
        message = action["payload"]
        message_type = message["type"]

        message_target = self.dispatch_map.get(message_type, None)

        if message_target is None:
            print(f"Chat dispatch error: No handler for {message_type}")
            return

        message_target["target"](message)

    def parse_chat(self, raw_message: str) -> dict:
        raw_split = raw_message.split("~")
        player = {
            "username": raw_split[0],
            "sigil": raw_split[1],
            "tag": raw_split[2],
            "level": raw_split[3],
        }
        message = raw_split[4]

        message_data = {
            "player": player,
            "message": message
        }

        return message_data

    def handle(self, action: dict):
        parsed_message = self.parse_chat(action["payload"])

        if parsed_message["message"][0] == "!":
            if parsed_message["message"][:8].lower() == "!luxbot:":
                self.handle_luxbot_command(parsed_message)

        print(parsed_message)

    def handle_luxbot_command(self, message):
        print("LuxBot command registered")
