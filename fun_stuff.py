import re

from multiprocessing.queues import Queue
from datetime import datetime

from repo import Repo
from utils import Utils
from calculator import Calculator


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
            "update_pets": {
                "target": self.update_pets
            },
            "import_command": {
                "target": self.import_command
            },
            "sigil_list": {
                "target": self.sigil_list
            },
            "better_calc": {
                "target": self.better_calc
            },
            "handle_yell": {
                "target": self.handle_yell
            },
        }

        self.calculator = Calculator()

    def dispatch(self, action: dict):
        target_dict = self.dispatch_map.get(action["action"], None)

        if target_dict is None:
            print(f"Fun dispatch error: No handler for {action['action']}")
            return

        target_dict["target"](action)

    # Pet link stuff
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

        reply_data = {
            "player": player["username"],
            "command": "pet_link",
            "payload": reply_string,
        }

        send_action = Utils.gen_send_action(request_source, reply_data)

        if send_action:
            self.p_q.put(send_action)
        else:
            print("fun_stuff error: Invalid source for send.")

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

        reply_data = {
            "player": player["username"],
            "command": "pet_link_by_title",
            "payload": reply_string,
        }

        send_action = Utils.gen_send_action(request_source, reply_data)

        if send_action:
            self.p_q.put(send_action)
        else:
            print("fun_stuff error: Invalid source for send.")

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

        paste_title = "Pet Photo List: {{ creation_local_datetime }}"

        new_action = {
            'target': 'api',
            'action': 'paste',
            'payload': {
                "data": output_string,
                "title": paste_title,
                "wrapper": f"{player['username'].capitalize()}, here's the pet photo list: " + "{{url}}",
                "player": player["username"],
                "command": "pet_stats"
            },
            'source': request_source
        }

        self.p_q.put(new_action)

    def update_pets(self, action: dict):
        command = action["payload"]
        player = command["player"]["username"]
        content = command["payload"]
        split_sub_command = content.split(";")
        if len(split_sub_command) != 4:
            print(f"Interactor:Response:Invalid syntax. (pets:add;pet;title;link)")
        else:
            subcommand = split_sub_command[0]
            pet = split_sub_command[1]
            title = split_sub_command[2]
            link = split_sub_command[3]

            pet_data = (title, pet, link)

            if subcommand == "add":
                self.db.add_pet(pet_data)
                print(f"{pet} link added with title: {title}")
    # End pet link stuff

    def dho_maps(self, action: dict):
        message = action["payload"]
        player = message["player"]
        request_source = action["source"]

        reply_string = f"Offline map solutions: https://prnt.sc/Mdd-AKMIHfLz"

        reply_data = {
            "player": player["username"],
            "command": "dho_maps",
            "payload": reply_string,
        }

        send_action = Utils.gen_send_action(request_source, reply_data)

        if send_action:
            self.p_q.put(send_action)
        else:
            print("fun_stuff error: Invalid source for send.")

    def wiki(self, action: dict):
        message = action["payload"]
        player = message["player"]
        request_source = action["source"]

        command = message["parsed_command"]

        if command['payload'] is not None:
            reply_string = f"Wiki page for {command['payload']}: https://idle-pixel.wiki/index.php/{command['payload']}"
        else:
            reply_string = f"Wiki home page: https://idle-pixel.wiki/index.php/Main_Page"

        reply_data = {
            "player": player["username"],
            "command": "wiki",
            "payload": reply_string,
        }

        send_action = Utils.gen_send_action(request_source, reply_data)

        if send_action:
            self.p_q.put(send_action)
        else:
            print("fun_stuff error: Invalid source for send.")

    def import_command(self, action: dict):
        message = action["payload"]
        player = message["player"]
        request_source = action["source"]
        command = message["parsed_command"]

        if command['payload'] != "antigravity":
            return

        reply_string = "https://xkcd.com/353"

        reply_data = {
            "player": player["username"],
            "command": "import",
            "payload": reply_string,
        }

        send_action = Utils.gen_send_action(request_source, reply_data)

        if send_action:
            self.p_q.put(send_action)
        else:
            print("fun_stuff error: Invalid source for send.")

    def sigil_list(self, action: dict):
        message = action["payload"]
        player = message["player"]
        request_source = action["source"]

        reply_string = f"{player['username'].capitalize()} here's (an out-dated) image of Lux's sigils: https://prnt.sc/zs7CX4WjB8q8"

        reply_data = {
            "player": player["username"],
            "command": "sigil_list",
            "payload": reply_string,
        }

        send_action = Utils.gen_send_action(request_source, reply_data)

        if send_action:
            self.p_q.put(send_action)
        else:
            print("fun_stuff error: Invalid source for send.")

    def better_calc(self, action):
        message = action["payload"]
        player = message["player"]
        request_source = action["source"]

        command = message["parsed_command"]

        if command['payload'] is not None:
            input_string = command["payload"]
        else:
            return

        result = self.calculator.calc(input_string)

        reply_string = f"{player['username'].capitalize()}, here is the result: {result}"

        reply_data = {
            "player": player["username"],
            "command": "better_calc",
            "payload": reply_string,
        }

        send_action = Utils.gen_send_action(request_source, reply_data)

        if send_action:
            self.p_q.put(send_action)
        else:
            print("fun_stuff error: Invalid source for send.")

    def handle_yell(self, action: dict):
        message = action["payload"]["payload"]

        reply_string = None

        if "agrodon" in message.lower():
            reply_string = "Wizard hax!"
        elif "nodorga" in message.lower():
            reply_string = "Wizard hax!"
        elif "i am smitty" in message.lower():
            reply_string = "Dev hax!"

        if not reply_string:
            return

        reply_data = {
            "player": "SERVER",
            "command": "yell_joke",
            "payload": reply_string,
        }

        send_action = Utils.gen_send_action("chat", reply_data)

        if send_action:
            self.p_q.put(send_action)
        else:
            print("fun_stuff error: Invalid source for send.")
