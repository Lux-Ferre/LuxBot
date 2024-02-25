from multiprocessing.queues import Queue
from datetime import datetime, timedelta

from repo import Repo
from utils import Utils


class Chat:
    def __init__(self, p_q: Queue, db: Repo):
        self.dispatch_map = {
            "pet": {
                "target_module": "fun",
                "target_command": "get_pet_link",
                "permission": 0,
                "help_string": "Replies with a random photo from the pets database. [!luxbot:pet <opt:pet_name>]",
            },
            "pet_title": {
                "target_module": "fun",
                "target_command": "get_pet_link_by_title",
                "permission": 0,
                "help_string": "Replies with a specific photo from the pets database. [!luxbot:pet_title <opt:title>]",
            },
            "dho_maps": {
                "target_module": "fun",
                "target_command": "dho_maps",
                "permission": 0,
                "help_string": "Replies with the solutions to the Offline treasure maps. [!luxbot:dho_maps]",
            },
            "wiki": {
                "target_module": "fun",
                "target_command": "wiki",
                "permission": 0,
                "help_string": "Replies with a link to the wiki (links are case sensitive.) [!luxbot:wiki <opt:page_title>]",
            },
            "pet_stats": {
                "target_module": "fun",
                "target_command": "pet_stats",
                "permission": 0,
                "help_string": "Replies with a pastebin link containing info about the pets database. [!luxbot:pet_stats]",
            },
            "import": {
                "target_module": "fun",
                "target_command": "import_command",
                "permission": 0,
                "help_string": "Easteregg. [!luxbot:import <REDACTED>]",
            },
            "sigil_list": {
                "target_module": "fun",
                "target_command": "sigil_list",
                "permission": 0,
                "help_string": "A screenshot of Lux's sigil collection. [!luxbot:sigil_list]",
            },
            "better_calc": {
                "target_module": "fun",
                "target_command": "better_calc",
                "permission": 1,
                "help_string": "Does basic arithmetical operations. [!luxbot:better_calc <expression>]",
            },
            "help": {
                "target_module": None,
                "target_command": None,
                "permission": 0,
                "help_string": "Replies with a list of chat commands or info on a specific command. [!luxbot:help <opt:command>]",
            },
        }
        self.p_q = p_q
        self.db = db
        self.last_com_time = datetime.min

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

        req = {"player": player["username"]}

        player["perm_level"] = self.db.permission_level(req)

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

        message = action["payload"]

        parsed_message = self.parse_chat(message["payload"])

        parsed_message["time"] = message["time"]

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

        cooldown_length = timedelta(minutes=1)
        current_time = datetime.now()
        elapsed_time = current_time - self.last_com_time

        if message["player"]["perm_level"] < 1 and elapsed_time < cooldown_length:
            print(f"{elapsed_time} < {cooldown_length}")
            return

        self.last_com_time = current_time

        req_perm = self.dispatch_map[parsed_command["command"]]["permission"]

        if message["player"]["perm_level"] < req_perm:
            print(f"{message['player']['username']}[{message['player']['perm_level']}] attempted command {parsed_command['command']}[{req_perm}]!")
            return

        if parsed_command["command"] == "help":
            self.handle_help_command(message)
        else:
            self.dispatch(message)

    def handle_help_command(self, message):
        payload = message["parsed_command"]["payload"]
        username = message["player"]["username"]

        chat_commands = self.dispatch_map

        if payload is None:
            help_string = "Command List"
            for com in chat_commands:
                help_string += f" | {com}"
        else:
            error_reply = {
                "help_string": f"Sorry {username}, {payload} is not a valid LuxBot command."
            }

            requested_command = chat_commands.get(payload, error_reply)

            help_string = requested_command["help_string"]

        reply_data = {
            "player": username,
            "command": "wiki",
            "payload": help_string,
        }

        send_action = Utils.gen_send_action("chat", reply_data)

        if send_action:
            self.p_q.put(send_action)
        else:
            print("Chat help error: Invalid source for send.")
        