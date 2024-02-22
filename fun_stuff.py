from multiprocessing.queues import Queue

from repo import Repo


class Fun:
    def __init__(self, p_q: Queue, db: Repo):
        self.p_q = p_q
        self.db = db
        self.dispatch_map = {
            "get_pet_link": {
                "target": self.get_pet_link
            }
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

        if parsed_command['payload'] is not None:
            query = "SELECT title, pet, link FROM pet_links WHERE pet=? ORDER BY RANDOM() LIMIT 1;"
            params = (parsed_command['payload'].lower(),)
        else:
            query = "SELECT title, pet, link FROM pet_links ORDER BY RANDOM() LIMIT 1;"
            params = tuple()

        query_data = {
            "query": query,
            "params": params,
            "many": False
        }

        pet_link = self.db.fetch_db(query_data)

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

        print(reply_string)
