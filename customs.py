from multiprocessing.queues import Queue


class Customs:
    def __init__(self, p_q: Queue):
        self.dispatch_map = {
            "send": {
                "target": self.send,
            },
            "close": {
                "target": self.close,
            },
            "print_items": {
                "target": self.print_items,
            },
            "echo": {
                "target": self.echo,
            }
        }
        self.p_q = p_q

    def dispatch(self, action: dict):
        if action["action"] == "send":
            self.send(action["payload"])
            return

        message = action["payload"]
        parsed_custom = self.parse(message["payload"])
        if parsed_custom["player"] != "a spider":
            print(f"{parsed_custom['player']} does not have access to customs.")
            return

        message_target = self.dispatch_map.get(parsed_custom["command"], None)

        if message_target is None:
            print(f"Custom message dispatch error: No handler for {parsed_custom['command']}")
            return

        message_target["target"](parsed_custom)

    def parse(self, raw_custom: str) -> dict:
        custom_data = {
            "player": None,
            "callback_id": None,
            "plugin": None,
            "command": None,
            "payload": None,
            "anwin_formatted": False,
        }
        player, data_string = raw_custom.split("~", 1)

        custom_data["player"] = player

        if data_string == "PLAYER_OFFLINE":
            custom_data["payload"] = data_string
            return custom_data

        split_data = raw_custom.split(":", 3)

        if len(split_data) >= 4:
            custom_data["callback_id"] = split_data[0]
            custom_data["plugin"] = split_data[1]
            custom_data["command"] = split_data[2]
            custom_data["payload"] = split_data[3]
            custom_data["anwin_formatted"] = True
        else:
            custom_data["payload"] = data_string

        return custom_data

    def send(self, custom_data: dict):
        player = custom_data.get("player", None)
        callback_id = custom_data.get("callback_id", "IPP0")
        plugin = custom_data.get("plugin", "LuxBot")
        command = custom_data.get("command", None)
        payload = custom_data.get("payload", "N/A")

        if player and command:
            custom_message = f"CUSTOM={player}~{callback_id}:{plugin}:{command}:{payload}"

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

    def close(self, custom_data: dict):
        if custom_data["payload"] == "close":
            action = {
                "target": "main",
                "action": "main_close",
                "payload": "",
                "source": "custom",
            }
        elif custom_data["payload"] == "restart":
            action = {
                "target": "main",
                "action": "main_restart",
                "payload": "",
                "source": "custom",
            }
        else:
            action = None

        if action:
            self.p_q.put(action)

    def print_items(self, custom_data: dict):
        action = {
            "target": "game",
            "action": "print_items",
            "payload": "",
            "source": "custom",
        }

        self.p_q.put(action)

    def echo(self, custom_data: dict):
        reply_data = {
            "player": custom_data["player"],
            "command": "Echo",
            "payload": custom_data["payload"],
        }

        action = {
            "target": "custom",
            "action": "send",
            "payload": reply_data,
            "source": "custom",
        }

        self.p_q.put(action)
