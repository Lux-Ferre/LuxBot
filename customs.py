import re

from multiprocessing.queues import Queue

from repo import Repo
from utils import Utils


class Customs:
    def __init__(self, p_q: Queue, db: Repo):
        self.dispatch_map = {
            "triggers": {
                "target_module": "mod",
                "target_command": "update_triggers",
                "permission": 3,
                "help_string": "Add/remove automod triggers. [triggers:add/remove;<trigger>]",
            },
            "speak": {
                "target_module": "admin",
                "target_command": "speak",
                "permission": 3,
                "help_string": "Sends a chat message [speak:<message>]",
            },
            "pets": {
                "target_module": "fun",
                "target_command": "update_pets",
                "permission": 3,
                "help_string": "Interacts with the pets database [pets:add;<pet>;<title>;<link>]",
            },
            "pet_title": {
                "target_module": "fun",
                "target_command": "get_pet_link_by_title",
                "permission": 0,
                "help_string": "Replies with a specific photo from the pets database. [pet_title:<title>]",
            },
            "update_cheaters": {
                "target_module": "admin",
                "target_command": "update_cheaters",
                "permission": 3,
                "help_string": "Updates cheater permission levels from Nades's list. [update_cheaters:*]",
            },
            "permissions": {
                "target_module": "admin",
                "target_command": "update_permissions",
                "permission": 3,
                "help_string": "Modifies player permissions. [permissions:<player>:<level>]",
            },
            "mute": {
                "target_module": "mod",
                "target_command": "mute",
                "permission": 3,
                "help_string": "Mutes target player. [mute:<player>;<reason>;<length>;<is_ip>]",
            },
            "whois": {
                "target_module": "mod",
                "target_command": "whois",
                "permission": 3,
                "help_string": "Runs a whois check on <player>, sending the result to all level 3 accounts. [whois:<player>]",
            },
            "addstat": {
                "target_module": "admin",
                "target_command": "add_stat",
                "permission": 3,
                "help_string": "Adds a new datapoint to the chat_stats stored in the database. [addstat:<datapoint_name>]",
            },
            "generic": {
                "target_module": "admin",
                "target_command": "generic_ws",
                "permission": 3,
                "help_string": "Relays content as a websocket frame. [generic:<ws_message>]",
            },
            "close": {
                "target_module": "admin",
                "target_command": "close_connection",
                "permission": 3,
                "help_string": "Closes websocket connection. [close:close/restart]",
            },
            "echo": {
                "target_module": None,
                "target_command": None,
                "permission": 3,
                "help_string": "Repeats the message back to the sender. [echo:<message>]",
            },
            "relay": {
                "target_module": None,
                "target_command": None,
                "permission": 3,
                "help_string": "Passes the message on to another player. [relay:<player>;<message>]",
            },
            "help": {
                "target_module": None,
                "target_command": None,
                "permission": 3,
                "help_string": "Lists commands(with 'none', or gives a description of a command. [help:none/<command>]",
            },
        }
        self.p_q = p_q
        self.db = db

    def dispatch(self, parsed_custom: dict):
        dispatch_target = self.dispatch_map.get(parsed_custom["command"], None)

        if dispatch_target is None:
            print(f"Custom message dispatch error: No handler for {parsed_custom['command']}")
            return

        new_payload = {
            "player": parsed_custom["player"],
            "parsed_command": {
                'callback_id': parsed_custom["callback_id"],
                'plugin': parsed_custom["plugin"],
                'command': parsed_custom["command"],
                'payload': parsed_custom["payload"],
                'anwin_formatted': parsed_custom["anwin_formatted"],
                'player_offline': parsed_custom["player_offline"],
            },

        }

        new_action = {
            "target": dispatch_target["target_module"],
            "action": dispatch_target["target_command"],
            "payload": new_payload,
            "source": "custom",
        }

        self.p_q.put(new_action)

    def parse_custom(self, raw_custom: str) -> dict:
        custom_data = {
            "player": None,
            "callback_id": None,
            "plugin": None,
            "command": None,
            "payload": None,
            "anwin_formatted": False,
            "player_offline": False
        }
        player, data_string = raw_custom.split("~", 1)

        custom_data["player"] = player

        if data_string == "PLAYER_OFFLINE":
            custom_data["payload"] = data_string
            custom_data["player_offline"] = True
            return custom_data

        split_data = data_string.split(":", 3)

        if len(split_data) >= 4:
            custom_data["callback_id"] = split_data[0]
            custom_data["plugin"] = split_data[1]
            custom_data["command"] = split_data[2]
            custom_data["payload"] = split_data[3]
            custom_data["anwin_formatted"] = True
        else:
            custom_data["payload"] = data_string

        return custom_data

    def handle(self, action: dict):
        if action["action"] == "send":
            self.send(action)
            return

        message = action["payload"]

        parsed_message = self.parse_custom(message["payload"])

        parsed_message["time"] = message["time"]
        player = parsed_message["player"]

        parsed_message["player"] = {
            "username": player,
            "perm_level": self.db.permission_level({"player": player})
        }

        if parsed_message["anwin_formatted"]:
            if parsed_message["plugin"] == "interactor":
                self.handle_luxbot_command(parsed_message)
        else:
            if parsed_message["player_offline"]:
                print(f"Player offline: {player}")
            else:
                print(f"Invalid custom, not Anwin Standard: {parsed_message}")

        print(parsed_message)

    def handle_luxbot_command(self, message: dict):
        player_perm = message["player"]["perm_level"]
        dispatch_data = self.dispatch_map.get(message["command"], None)
        if not dispatch_data:
            print(f"Custom error: Command '{message['command']}' does not exist!")
            return

        req_perm = self.dispatch_map[message["command"]]["permission"]

        if player_perm < req_perm:
            print(f"{message['player']['username']}[{player_perm}] attempted custom {message['command']}[{req_perm}]!")
            return

        match message["command"]:
            case "echo":
                self.echo(message)
            case "relay":
                self.relay(message)
            case "help":
                self.handle_help_command(message)
            case _:
                self.dispatch(message)

    def send(self, action: dict):
        custom_data = action["payload"]
        player = custom_data.get("player", None)
        callback_id = custom_data.get("callback_id", "IPP0")
        plugin = custom_data.get("plugin", "LuxBot")
        command = custom_data.get("command", None)
        payload = custom_data.get("payload", "N/A")

        leading_data = f"CUSTOM={player}~{callback_id}:{plugin}:{command}:"

        payload_max_length = 120 - len(leading_data)

        print(payload)

        paginated_payload = re.findall(".{1," + f"{payload_max_length}" + "}", payload)

        if player and command:
            for page in paginated_payload:
                custom_message = f"{leading_data}:{page}"

                action = {
                    "target": "game",
                    "action": "send_ws_message",
                    "payload": custom_message,
                    "source": "custom",
                }

                self.p_q.put(action)
        else:
            print("Invalid custom send:")
            print(custom_data)

    def echo(self, custom_data: dict):
        reply_data = {
            "player": custom_data["player"]["username"],
            "command": "Echo",
            "payload": custom_data["payload"],
        }

        send_action = Utils.gen_send_action("custom", reply_data)

        self.p_q.put(send_action)

    def relay(self, custom_data: dict):
        split_data = custom_data["payload"].split(";", maxsplit=1)
        if len(split_data) != 2:
            print(f"Invalid relay command: {custom_data}")
            return

        reply_data = {
            "player": split_data[0],
            "command": "Relay",
            "payload": split_data[1],
        }

        send_action = Utils.gen_send_action("custom", reply_data)

        self.p_q.put(send_action)

    def handle_help_command(self, message):
        payload = message["payload"]
        player = message["player"]

        custom_commands = self.dispatch_map

        if payload is None or payload.lower() == "none":
            help_string = "Command List"
            for com in custom_commands:
                help_string += f" | {com}"
        else:
            error_reply = {
                "help_string": f"Sorry {player['username']}, {payload} is not a valid LuxBot command."
            }

            requested_command = custom_commands.get(payload, error_reply)

            help_string = requested_command["help_string"]

        reply_data = {
            "player": player["username"],
            "command": "help",
            "payload": help_string,
        }

        send_action = Utils.gen_send_action("custom", reply_data)

        if send_action:
            self.p_q.put(send_action)
        else:
            print("Custom help error: Invalid source for send.")
