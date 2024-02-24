from multiprocessing.queues import Queue

from repo import Repo


class Chat:
    def __init__(self, p_q: Queue, db: Repo):
        self.dispatch_map = {
            "pet": {
                "target_module": "fun",
                "target_command": "get_pet_link",
                "permission": 0,
                "help_string": "",
            },
            "pet_title": {
                "target_module": "fun",
                "target_command": "get_pet_link_by_title",
                "permission": 0,
                "help_string": "",
            },
            "dho_maps": {
                "target_module": "fun",
                "target_command": "dho_maps",
                "permission": 0,
                "help_string": "",
            },
            "wiki": {
                "target_module": "fun",
                "target_command": "wiki",
                "permission": 0,
                "help_string": "",
            },
            "pet_stats": {
                "target_module": "fun",
                "target_command": "pet_stats",
                "permission": 0,
                "help_string": "",
            },
            "import": {
                "target_module": "fun",
                "target_command": "import_command",
                "permission": 0,
                "help_string": "",
            },
            "sigil_list": {
                "target_module": "fun",
                "target_command": "sigil_list",
                "permission": 0,
                "help_string": "",
            },
        }
        self.p_q = p_q
        self.db = db

    def dispatch(self, message: dict):
        command = message["parsed_command"]["command"]
        dispatch_target = self.dispatch_map.get(command, None)

        if dispatch_target is None:
            print(f"Chat dispatch error: No handler for {command}")
            return

        new_action = {
                    "target": dispatch_target["target_module"],
                    "action": dispatch_target["target_command"],
                    "payload": message,
                    "source": "chat",
        }

        self.p_q.put(new_action)

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
        if action["action"] == "send":
            self.send(action)
            return

        parsed_message = self.parse_chat(action["payload"])

        if parsed_message["message"][0] == "!":
            if parsed_message["message"][:8].lower() == "!luxbot:":
                self.handle_luxbot_command(parsed_message)

        print(parsed_message)

    def send(self, action: dict):
        message = f"CHAT={action['payload']['payload']}"

        action = {
            "target": "game",
            "action": "send_ws_message",
            "payload": message,
            "source": "chat",
        }

        self.p_q.put(action)

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

        self.dispatch(message)
        