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

    def parse_luxbot_command(self, raw_message):
        split_message = raw_message.split(" ", 1)  # !luxbot:command payload @message -> ['!luxbot:command', 'payload @message']

        trigger_and_command = split_message[0]
        split_command = trigger_and_command.split(":", 1)
        command = split_command[1].lower()

        payload = None
        at_message = None

        if len(split_message) > 1:
            split_at = split_message[1].split("@", 1)
            payload = split_at[0].strip()
            if payload == "":  # Handle case of message and no payload
                payload = None
            if len(split_at) > 1:
                at_message = split_at[1]

        parsed_command = {
            "command": command,
            "payload": payload,
            "at_message": at_message,
        }

        return parsed_command

    def handle_luxbot_command(self, message: dict):
        parsed_command = self.parse_luxbot_command(message["message"])
        message["parsed_command"] = parsed_command

        match parsed_command["command"]:
            case "pet":
                action = {
                    "target": "fun",
                    "action": "get_pet_link",
                    "payload": message,
                    "source": "chat",
                }

                self.p_q.put(action)
            case "pet_title":
                action = {
                    "target": "fun",
                    "action": "get_pet_link_by_title",
                    "payload": message,
                    "source": "chat",
                }

                self.p_q.put(action)

