from multiprocessing.queues import Queue

from repo import Repo


class Fun:
    def __init__(self, p_q: Queue, db: Repo):
        self.p_q = p_q
        self.db = db
        self.dispatch_map = {
            "get_pet_link": {
                "target": self.get_pet_link
            },
            "get_pet_link_by_title": {
                "target": self.get_pet_link_by_title
            },
        }

    def dispatch(self, action: dict):
        target_dict = self.dispatch_map.get(action["action"], None)

        if target_dict is None:
            print(f"Fun dispatch error: No handler for {action['action']}")
            return

        target_dict["target"](action)

    def get_pet_link(self, action: dict):
        message = action["payload"]
        parsed_command = message["parsed_command"]
        player = message["player"]
        request_source = action["source"]

        req = {"pet": parsed_command['payload']}

        pet_link = self.db.get_pet_link(req)

        if pet_link is None:
            reply_string = f"Sorry {player['username'].capitalize()}, that is an invalid pet name."
        else:
            reply_string = f"{player['username'].capitalize()}, your random pet is {pet_link[1].capitalize()}! {pet_link[0].capitalize()}: {pet_link[2]}"

        if request_source == "chat":
            reply_data = {
                "player": player["username"],
                "command": "pet_link",
                "payload": reply_string,
            }

            action = {
                "target": "custom",
                "action": "send",
                "payload": reply_data,
                "source": "custom",
            }

            self.p_q.put(action)

    def get_pet_link_by_title(self, action: dict):
        message = action["payload"]
        parsed_command = message["parsed_command"]
        player = message["player"]
        request_source = action["source"]

        req = {"title": parsed_command['payload']}

        pet_link = self.db.get_pet_link_by_title(req)

        if pet_link is None:
            reply_string = f"Sorry {player['username'].capitalize()}, that is an invalid pet image title."
        else:
            reply_string = f"{player['username'].capitalize()}, your requested pet is {pet_link[1].capitalize()}! {pet_link[0].capitalize()}: {pet_link[2]}"

        if request_source == "chat":
            reply_data = {
                "player": player["username"],
                "command": "pet_link",
                "payload": reply_string,
            }

            action = {
                "target": "custom",
                "action": "send",
                "payload": reply_data,
                "source": "custom",
            }

            self.p_q.put(action)
