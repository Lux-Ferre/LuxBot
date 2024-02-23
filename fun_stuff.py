from multiprocessing.queues import Queue

from repo import Repo
from utils import Utils


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
            "dho_maps": {
                "target": self.dho_maps
            },
            "wiki": {
                "target": self.wiki
            },
            "pet_stats": {
                "target": self.pet_stats
            },
            "import_command": {
                "target": self.import_command
            },
            "sigil_list": {
                "target": self.sigil_list
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
                "target": "chat",
                "action": "send",
                "payload": reply_data,
                "source": "chat",
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
                "target": "chat",
                "action": "send",
                "payload": reply_data,
                "source": "chat",
            }

            self.p_q.put(action)

    def dho_maps(self, action: dict):
        message = action["payload"]
        player = message["player"]
        request_source = action["source"]

        reply_string = f"Offline map solutions: https://prnt.sc/Mdd-AKMIHfLz"

        if request_source == "chat":
            reply_data = {
                "player": player["username"],
                "command": "dho_maps",
                "payload": reply_string,
            }

            action = {
                "target": "chat",
                "action": "send",
                "payload": reply_data,
                "source": "chat",
            }

            self.p_q.put(action)

    def wiki(self, action: dict):
        message = action["payload"]
        player = message["player"]
        request_source = action["source"]

        command = message["parsed_command"]

        if command['payload'] is not None:
            reply_string = f"Wiki page for {command['payload']}: https://idle-pixel.wiki/index.php/{command['payload']}"
        else:
            reply_string = f"Wiki home page: https://idle-pixel.wiki/index.php/Main_Page"

        if request_source == "chat":
            reply_data = {
                "player": player["username"],
                "command": "wiki",
                "payload": reply_string,
            }

            action = {
                "target": "chat",
                "action": "send",
                "payload": reply_data,
                "source": "chat",
            }

            self.p_q.put(action)

    def pet_stats(self, action: dict):
        message = action["payload"]
        player = message["player"]
        request_source = action["source"]

        all_stats = self.db.get_pet_stats()

        output_string = ""

        for stat in all_stats:
            pet, title_string = stat
            titles = title_string.split(",")
            title_count = len(titles)
            output_string += f"{pet.capitalize()}({title_count}):\n"
            for title in titles:
                output_string += f"\t{title.capitalize()}\n"

        pastebin_url = Utils.dump_to_pastebin(output_string, "10M")

        reply_string = f"{pastebin_url}"

        if request_source == "chat":
            reply_data = {
                "player": player["username"],
                "command": "pet_stats",
                "payload": reply_string,
            }

            action = {
                "target": "chat",
                "action": "send",
                "payload": reply_data,
                "source": "chat",
            }

            self.p_q.put(action)

    def import_command(self, action: dict):
        message = action["payload"]
        player = message["player"]
        request_source = action["source"]
        command = message["parsed_command"]

        if command['payload'] != "antigravity":
            return

        reply_string = "https://xkcd.com/353"

        if request_source == "chat":
            reply_data = {
                "player": player["username"],
                "command": "import",
                "payload": reply_string,
            }

            action = {
                "target": "chat",
                "action": "send",
                "payload": reply_data,
                "source": "chat",
            }

            self.p_q.put(action)

    def sigil_list(self, action: dict):
        message = action["payload"]
        player = message["player"]
        request_source = action["source"]

        reply_string = f"{player['username'].capitalize()} here's (an out-dated) image of Lux's sigils: https://prnt.sc/zs7CX4WjB8q8"

        if request_source == "chat":
            reply_data = {
                "player": player["username"],
                "command": "sigil_list",
                "payload": reply_string,
            }

            action = {
                "target": "chat",
                "action": "send",
                "payload": reply_data,
                "source": "chat",
            }

            self.p_q.put(action)
