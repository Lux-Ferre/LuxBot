import requests
import json

from multiprocessing.queues import Queue

from repo import Repo
from utils import Utils


class Admin:
    def __init__(self, p_q: Queue, db: Repo):
        self.p_q = p_q
        self.db = db
        self.dispatch_map = {
            "speak": {
                "target": self.speak
            },
            "update_cheaters": {
                "target": self.update_cheaters
            },
            "permissions": {
                "target": self.permissions
            },
            "add_stat": {
                "target": self.add_stat
            },
            "generic": {
                "target": self.generic
            },
            "close": {
                "target": self.close
            },
        }

    def dispatch(self, action: dict):
        target_dict = self.dispatch_map.get(action["action"], None)

        if target_dict is None:
            print(f"Admin dispatch error: No handler for {action['action']}")
            return

        target_dict["target"](action)

    def speak(self, action: dict):
        # {'payload': {'player': {'username': '', 'perm_level': 3}, 'parsed_command': {}}}
        message = action["payload"]
        parsed_command = message["parsed_command"]
        player = message["player"]

        reply_string = parsed_command["payload"]

        reply_data = {
            "player": player["username"],
            "command": "pet_link",
            "payload": reply_string,
        }

        send_action = Utils.gen_send_action("chat", reply_data)

        if send_action:
            self.p_q.put(send_action)
        else:
            print("admin_stuff error: Invalid source for send.")

    def update_cheaters(self, action: dict):
        url = 'https://raw.githubusercontent.com/GodofNades/idle-pixel/main/AltTraders.json'
        resp = requests.get(url)
        data = json.loads(resp.text)

        cheater_list = []
        for data_point in data:
            cheater_list.append(data_point["name"])

        self.db.set_cheaters_permissions({"cheater_list": cheater_list})

    def permissions(self, action: dict):
        pass

    def add_stat(self, action: dict):
        pass

    def generic(self, action: dict):
        pass

    def close(self, action: dict):
        pass
