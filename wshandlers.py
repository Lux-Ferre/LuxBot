from multiprocessing.queues import Queue


class WSHandlers:
    def __init__(self, p_q: Queue):
        self.dispatch_map = {}
        self.p_q = p_q

    def apply_dispatch_map(self, new_map: dict = None):
        if new_map is not None:
            self.dispatch_map = new_map
        else:
            self.dispatch_map = {
                "CHAT": {
                    "target": self.on_chat,
                },
                "YELL": {
                    "target": self.on_yell,
                },
                "CUSTOM": {
                    "target": self.on_custom,
                },
                "SET_ITEMS": {
                    "target": self.on_set_items,
                },
                "OPEN_DIALOGUE": {
                    "target": self.on_dialogue
                }
            }

    def dispatch(self, action: dict):
        message = action["payload"]
        message_type = message["type"]

        message_target = self.dispatch_map.get(message_type, None)

        if message_target is None:
            print(f"Dispatch error: No handler for {message_type}")
            return

        message_target["target"](message)

    def on_chat(self, message: dict):
        action = {
            "target": "chat",
            "action": "handle",
            "payload": message,
            "source": "chat",
        }

        self.p_q.put(action)

    def on_yell(self, message: dict):
        action = {
            "target": "stats",
            "action": "handle_yell",
            "payload": message,
            "source": "ws_handlers",
        }

        self.p_q.put(action)

    def on_custom(self, message: dict):
        action = {
            "target": "custom",
            "action": "parse_and_dispatch",
            "payload": message,
            "source": "ws_handlers",
        }
        self.p_q.put(action)

    def on_set_items(self, message: dict):
        split_vars = message["payload"].split("~")
        parsed_vars = {}
        for i in range(0, len(split_vars), 2):
            key = split_vars[i]
            value = split_vars[i+1]
            if value.isnumeric():
                value = int(value)
            else:
                if value[0] == "-":
                    if value[1:].isnumeric():
                        value = -abs(int(value[1:]))
            parsed_vars[key] = value

        action = {
            "target": "game",
            "action": "set_items",
            "payload": parsed_vars,
            "source": "ws_handlers",
        }

        self.p_q.put(action)

    def on_dialogue(self, message: dict):
        data = message["payload"]
        if data[:5] == "WHOIS":
            cropped_data = data[15:]
            whois_list = cropped_data.split("<br />")[:-1]

            whois_string = ",".join(whois_list)

            action = {
                "target": "mod",
                "action": "received_whois",
                "payload": whois_string,
                "source": "ws_handlers"
            }

            self.p_q.put(action)
        else:
            print(f"DIALOGUE: {data}")
