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
                },
                "VALID_LOGIN": {
                    "target": self.on_valid_login
                },
                "EVENT_GLOBAL_PROGRESS": {
                    "target": self.on_event_global_progress
                },
                "REFRESH_TCG": {
                    "target": self.on_refresh_tcg
                }
            }

    def dispatch(self, action: dict):
        message = action["payload"]
        message_type = message["type"]

        ignored_types = ["SET_COUNTRY"]

        if message_type in ignored_types:
            return

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
        actions = [
            {
                "target": "stats",
                "action": "handle_yell",
                "payload": message,
                "source": "ws_handlers",
            },
            {
                "target": "fun",
                "action": "handle_yell",
                "payload": message,
                "source": "ws_handlers",
            },
        ]

        for action in actions:
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

        actions = [
            {
                "target": "game",
                "action": "set_items",
                "payload": parsed_vars,
                "source": "ws_handlers",
            },
            {
                "target": "event",
                "action": "handle_set_items",
                "payload": parsed_vars,
                "source": "ws_handlers",
            }
        ]
        for action in actions:
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
        elif data[:12] == "OFFLINE TIME":
            start = data.index("for:") + 13
            end = data.index("</b>", start)
            print(f"Offline time: {data[start:end]}")
        else:
            print(f"DIALOGUE: {data}")

    def on_valid_login(self, message: dict):
        print("Signature verified. Login Successful.")
        action = {
            "target": "game",
            "action": "set_ws_active",
            "payload": message,
            "source": "ws_handlers",
        }
        self.p_q.put(action)

    def on_event_global_progress(self, message: dict):
        action = {
            "target": "event",
            "action": "handle_event_progress",
            "payload": message,
            "source": "ws_handlers",
        }
        self.p_q.put(action)

    def on_refresh_tcg(self, message: dict):
        action = {
            "target": "tcg",
            "action": "handle_refresh_tcg",
            "payload": message,
            "source": "ws_handlers",
        }
        self.p_q.put(action)

