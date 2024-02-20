from multiprocessing.queues import Queue


class Chat:
    def __init__(self, p_q: Queue):
        self.dispatch_map = {
            "handle": {
                "target": self.handle,
            }
        }
        self.p_q = p_q

    def dispatch(self, action: dict):
        message = action["payload"]
        message_type = message["type"]

        message_target = self.dispatch_map.get(message_type, None)

        if message_target is None:
            print(f"Chat dispatch error: No handler for {message_type}")
            return

        message_target["target"](message)

    def parse(self, raw_message: str) -> dict:
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
        parsed_message = self.parse(action["payload"])

        print(parsed_message)
