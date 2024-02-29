import random

from multiprocessing.queues import Queue

from repo import Repo
from utils import Utils, RepeatTimer


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
            },
            "handle_modmod": {
                "target": self.handle_modmod
            },
            "handle_offline_mod": {
                "target": self.handle_offline_mod
            },
            "handle_at_mods": {
                "target": self.handle_at_mods
            },
            "handle_automod": {
                "target": self.handle_automod
            },
        }
        self.modmod_dispatch_map = {
            "HELLO": {
                "target": self.modmod_hello,
            },
            "MODCHAT": {
                "target": self.modmod_modchat,
            },
            "context": {
                "target": self.modmod_context,
            },
            "automod": {
                "target": self.modmod_automod,
            },
        }
        self.whois_requester = None
        self.online_mods = set()

        mod_poll_timer = RepeatTimer(60, self.poll_online_mods)
        mod_poll_timer.start()

    def dispatch(self, action: dict):
        target_dict = self.dispatch_map.get(action["action"], None)

        if target_dict is None:
            print(f"Mod dispatch error: No handler for {action['action']}")
            return

        target_dict["target"](action)

    # ModMod Stuff
    def handle_modmod(self, action: dict):
        parsed_custom = action["payload"]
        target_dict = self.modmod_dispatch_map.get(parsed_custom["command"], None)

        self.online_mods.add(parsed_custom["player"]["username"])

        if target_dict is None:
            print(f"ModMod dispatch error: No handler for {parsed_custom['command']}")
            return

        new_payload = {
            "player": parsed_custom["player"],
            "parsed_command": {
                'callback_id': parsed_custom["callback_id"],
                'plugin': parsed_custom["plugin"],
                'command': parsed_custom["command"],
                'payload': parsed_custom["payload"],
                'anwin_formatted': parsed_custom["anwin_formatted"],
                'player_offline': parsed_custom["player_offline"],
                "time": parsed_custom["time"],
            },
        }

        new_action = {
            "target": "modmod",
            "action": parsed_custom["command"],
            "payload": new_payload,
            "source": "custom",
        }

        target_dict["target"](new_action)

    def send_modmod_message(self, message_data: dict):
        if message_data["player"] == "ALL":
            mods = list(self.online_mods)
        else:
            mods = [message_data["player"]]

        for mod in mods:
            send_data = {
                "player": mod,
                "plugin": "ModMod",
                "command": message_data["command"],
                "payload": message_data["payload"],
            }

            send_action = Utils.gen_send_action("custom", send_data)

            if send_action:
                self.p_q.put(send_action)
            else:
                print("mod_stuff error: Invalid source for send.")

    def modmod_hello(self, action: dict):
        if action['payload']['parsed_command']['payload'] == "1:0":
            message_data = {
                "player": "ALL",
                "command": "login",
                "payload": f"{action['payload']['player']['username']}",
            }

            self.send_modmod_message(message_data)

            mod_string = ""
            for mod in self.online_mods:
                mod_string += f"{mod},"

            message_data = {
                "player": f"{action['payload']['player']['username']}",
                "command": "list",
                "payload": f"{mod_string[:-1]}",
            }

            self.send_modmod_message(message_data)

    def modmod_modchat(self, action: dict):
        message_data = {
            "player": "ALL",
            "command": "message",
            "payload": f"{action['payload']['player']['username']}: {action['payload']['parsed_command']['payload']}",
        }

        self.send_modmod_message(message_data)

    def modmod_context(self, action: dict):
        message_data = {
            "player": "ALL",
            "command": "context",
            "payload": f"{action['payload']['parsed_command']['payload']}",
        }

        self.send_modmod_message(message_data)

    def modmod_automod(self, action: dict):
        message_data = {
            "player": "ALL",
            "command": "automod",
            "payload": f"{action['payload']['parsed_command']['payload']}",
        }

        self.send_modmod_message(message_data)

    def handle_at_mods(self, action: dict):
        message = action["payload"]["message"]
        player = action["payload"]["player"]["username"]

        if message[:5] != "@mods":
            return

        note = message[5:]
        mod_call = f"{player} is calling for a mod with note: {note}"

        message_data = {
            "player": "ALL",
            "command": "at",
            "payload": f"{mod_call}",
        }

        self.send_modmod_message(message_data)
    # End ModMod Stuff

    def poll_online_mods(self):
        message_data = {
            "player": "ALL",
            "command": "HELLO",
            "payload": f"0:0",
        }

        self.send_modmod_message(message_data)

    def handle_offline_mod(self, action: dict):
        player = action['payload']['player']['username']

        if player not in self.online_mods:
            return

        try:
            self.online_mods.remove(player)
        except ValueError:
            pass

        message_data = {
            "player": "ALL",
            "command": "logout",
            "payload": f"{player}",
        }

        self.send_modmod_message(message_data)

    def handle_automod(self, action: dict):
        player = action['payload']['player']
        message = action["payload"]["message"]
        flag_words_dict = self.db.read_config_row({"key": "automod_flag_words"})

        automod_replies = [
            f"{player['username']} has been axed from chat.",
            f"{player['username']} has been defenestrated.",
            f"Buh-bye {player['username']}!",
            "𝔹 𝕆 ℕ 𝕂 !",
            f"{player['username']} is taking an enforced break from chat.",
            f"( ◡̀_◡́)▬▬█",
            f"ᕙ( ︡’︡ 益 ’︠)ง▬▬█",
            f"█▬▬ ◟(`ﮧ´ ◟ )",
        ]

        automod_flag_words = flag_words_dict["word_list"].split(",")
        automod_flag_words += [" fag", "fag "]
        message = message.lower()
        for trigger in automod_flag_words:
            if trigger in message:
                bot_list = {"botofnades": "BotofNades", "wikisearch": "WikiSearch"}
                if player["username"] in bot_list:
                    reply_string = f"Silly {bot_list[player['username']]}, you shouldn't copy the fleshbags' bad words. I forgive you though."
                    send_action = Utils.gen_send_action("chat", {"payload": reply_string})
                    self.p_q.put(send_action)
                    return

                message_data = {
                    "player": "ALL",
                    "command": "automod",
                    "payload": f"**{player['username']} has been muted for using the word: {trigger}**",
                }

                self.send_modmod_message(message_data)

                target = player['username']
                length = "24"
                reason = f'Using the word: {trigger}: "{message}"'
                is_ip = "false"
                actions = [
                    Utils.gen_mute_action(target, length, reason, is_ip),
                    Utils.gen_send_action("chat", {"payload": random.choice(automod_replies)})
                ]

                for new_action in actions:
                    self.p_q.put(new_action)
                return

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
