from multiprocessing.queues import Queue

from repo import Repo
from utils import Utils


class Mod:
    def __init__(self, p_q: Queue, db: Repo):
        self.p_q = p_q
        self.db = db
        self.dispatch_map = {
            "update_triggers": {
                "target": self.update_triggers
            },
            "mute": {
                "target": self.mute
            },
            "whois": {
                "target": self.request_whois
            },
            "received_whois": {
                "target": self.received_whois
            }
        }
        self.whois_requester = None

    def dispatch(self, action: dict):
        target_dict = self.dispatch_map.get(action["action"], None)

        if target_dict is None:
            print(f"Mod dispatch error: No handler for {action['action']}")
            return

        target_dict["target"](action)

    def update_triggers(self, action: dict):
        # {'payload': {'player': {'username': '', 'perm_level': 3}, 'parsed_command': {}}}
        player = action["payload"]["player"]["username"]
        command_data = action["payload"]["parsed_command"]
        payload = command_data["payload"]

        flag_words_dict = self.db.read_config_row({"key": "automod_flag_words"})
        trigger_list = flag_words_dict["word_list"].split(",")

        split_command = payload.split(";")
        subcommand = split_command[0]
        changed_trigger = split_command[1]

        if subcommand == "add":
            trigger_list.append(changed_trigger.strip())
            trigger_dict = {"word_list": ",".join(trigger_list)}
            db_payload = {
                "key": "automod_flag_words",
                "value": trigger_dict
            }
            self.db.set_config_row(db_payload)
        elif subcommand == "remove":
            trigger_list.remove(changed_trigger.strip())
            trigger_dict = {"word_list": ",".join(trigger_list)}
            db_payload = {
                "key": "automod_flag_words",
                "value": trigger_dict
            }
            self.db.set_config_row(db_payload)

    def mute(self, action: dict):
        # {'payload': {'player': {'username': '', 'perm_level': 3}, 'parsed_command': {}}}
        player = action["payload"]["player"]["username"]
        command_data = action["payload"]["parsed_command"]
        payload = command_data["payload"]

        if payload is None:
            print(f"Invalid mute format: {payload}")
            return
        else:
            split_data = payload.split(";")

        if len(split_data) != 4:
            print(f"Invalid mute format: {payload}")
            return

        target = split_data[0]
        reason = split_data[1]
        length = split_data[2]
        is_ip = split_data[3]

        mute_action = Utils.gen_mute_action(target, length, reason, is_ip)

        self.p_q.put(mute_action)

    def request_whois(self, action: dict):
        # {'payload': {'player': {'username': '', 'perm_level': 3}, 'parsed_command': {}}}
        player = action["payload"]["player"]["username"]
        command_data = action["payload"]["parsed_command"]
        payload = command_data["payload"]

        if payload is None:
            print(f"Invalid whois syntax: {payload}")
            return

        self.whois_requester = player

        mute_send_data = {
            "player": player,
            "command": "help",
            "payload": f"/whois {payload}",
        }

        chat_send_action = Utils.gen_send_action("chat", mute_send_data)

        self.p_q.put(chat_send_action)

    def received_whois(self, action: dict):
        if self.whois_requester is None:
            return

        whois_list = action["payload"]

        reply_data = {
            "player": self.whois_requester,
            "command": "whois",
            "payload": whois_list,
        }

        self.whois_requester = None

        send_action = Utils.gen_send_action("custom", reply_data)

        self.p_q.put(send_action)
