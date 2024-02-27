import re

from multiprocessing.queues import Queue

from repo import Repo
from utils import Utils


class Stats:
    def __init__(self, p_q: Queue, db: Repo):
        self.p_q = p_q
        self.db = db
        self.dispatch_map = {
            "handle_chat": {
                "target": self.handle_chat
            },
            "handle_yell": {
                "target": self.handle_yell
            },
            "get_specific_stat": {
                "target": self.get_specific_stat
            },
            "get_all_stats": {
                "target": self.get_all_stats
            },
            "get_amy_stats": {
                "target": self.get_amy_stats
            },
            "get_one_life_stats": {
                "target": self.get_one_life_stats
            },
        }

    def dispatch(self, action: dict):
        target_dict = self.dispatch_map.get(action["action"], None)

        if target_dict is None:
            print(f"Stats dispatch error: No handler for {action['action']}")
            return

        target_dict["target"](action)

    @staticmethod
    def __per_time(total_time: int, stat_count: int) -> tuple[int, float, float]:
        """
        Takes a time in seconds(int) and a stat_count(int),
        returns tuple of stat_count(int), count_per_day(float), count_per_hour(float)
        """
        number_of_hours = round(total_time / 3600)
        number_of_days = round(number_of_hours / 24)

        if number_of_hours == 0:
            count_per_hour = 0
        else:
            count_per_hour = round(stat_count / number_of_hours, 3)

        if number_of_days == 0:
            count_per_day = 0
        else:
            count_per_day = round(stat_count / number_of_days, 3)

        return stat_count, count_per_day, count_per_hour

    def handle_chat(self, action: dict):
        # {'target': 'stats', 'action': 'handle_chat', 'payload': {'player': {'username': '', 'sigil': '', 'tag': '', 'level': '', 'perm_level': 0}, 'message': '', 'time': datetime}, 'source': 'chat'}
        message_data = action["payload"]
        self.update_stats_from_chat(message_data)
        self.handle_dynamic_command(message_data)

    def handle_yell(self, action: dict):
        # {'target': 'stats', 'action': 'handle_yell', 'payload': {'type': 'YELL', 'payload': '', 'time': datetime}, 'source': 'ws_handlers'}
        yell_data = action["payload"]
        yell_text = yell_data["payload"]
        yell_type = self.get_yell_type(yell_text)

        self.update_stats_from_yell(yell_type)

        if yell_type == "one_life_death":
            self.update_one_life(yell_data)

    def handle_dynamic_command(self, action: dict):
        pass

    @staticmethod
    def get_yell_type(message: str) -> str:
        if "found a diamond" in message:
            yell_type = "diamond"
        elif "found a legendary blood diamond" in message:
            yell_type = "blood_diamond"
        elif "encountered a gem goblin" in message:
            yell_type = "gem_goblin"
        elif "encountered a blood gem goblin" in message:
            yell_type = "blood_goblin"
        elif "looted a monster sigil" in message:
            yell_type = "sigil"
        elif "has just reached level 100" in message:
            yell_type = "max_level"
        elif "has completed the elite" in message:
            yell_type = "elite_achievement"
        elif "gold armour" in message:
            yell_type = "gold_armour"
        elif "lost 1-Life Hardcore status" in message:
            yell_type = "one_life_death"
        else:
            yell_type = "unknown"

        return yell_type

    def update_stats_from_chat(self, message_data: dict):
        player = message_data["player"]
        message = message_data["message"]
        amy_accounts = [
            "amyjane1991",
            "youallsuck",
            "freeamyhugs",
            "amybear",
            "zombiebunny",
            "idkwat2put",
            "skyedemon",
            "iloveamy",
            "demonlilly",
            "youarenoob",
        ]

        current_stats = self.db.read_config_row({"key": "chat_stats"})

        current_stats["total_messages"] += 1

        if len(message) < 1:
            return

        if "noob" in message:
            current_stats["total_noobs"] += 1

        if player["username"] in amy_accounts:
            current_stats["amy_total"] += 1

            if message[0] != "!":
                if "noob" in message:
                    current_stats["amy_noobs"] += 1

                if "suck" in message:
                    current_stats["amy_sucks"] += 1

        if message[:5] == "?wiki":  # 30/10/23 14:00
            current_stats["wikibot"] += 1

        if message[0] == "!":
            if message[:7] == "!hevent":
                current_stats["hevent"] += 1
            elif message[:6] == "!zombo":
                current_stats["zombo"] += 1
                if current_stats["zombo"] % 100 == 0:
                    reply_string = f"{player['username'].capitalize()} just made request number {current_stats['zombo']} to the !zombo command! (Since I started tracking)"
                    reply_data = {
                        "player": player["username"],
                        "command": "zombo",
                        "payload": reply_string,
                    }
                    send_action = Utils.gen_send_action("chat", reply_data)

                    if send_action:
                        self.p_q.put(send_action)
                    else:
                        print("stats_stuff error: Invalid source for send.")

            if message[:7] == "!luxbot":
                current_stats["luxbot_requests"] += 1
            else:
                current_stats["botofnades_requests"] += 1

        update_data = {
            "key": "chat_stats",
            "value": current_stats
        }
        self.db.set_config_row(update_data)

    def update_stats_from_yell(self, yell_type: str):
        current_stats = self.db.read_config_row({"key": "chat_stats"})

        current_stats["total_yells"] += 1

        match yell_type:
            case "diamond":
                current_stats["diamonds_found"] += 1
            case "blood_diamond":
                current_stats["blood_diamonds_found"] += 1
            case "gem_goblin":
                current_stats["gem_goblin_encounters"] += 1
            case "blood_goblin":
                current_stats["blood_goblin_encounters"] += 1
            case "sigil":
                current_stats["sigils_found"] += 1
            case "max_level":
                current_stats["max_levels"] += 1
            case "elite_achievement":
                current_stats["elite_achievements"] += 1
            case "gold_armour":
                current_stats["gold_armour"] += 1
            case "one_life_death":
                current_stats["oneLifeDeaths"] += 1
            case _:
                pass

        update_data = {
            "key": "chat_stats",
            "value": current_stats
        }
        self.db.set_config_row(update_data)

    def update_one_life(self, action: dict):
        pass

    def get_specific_stat(self, action: dict):
        pass

    def get_all_stats(self, action: dict):
        pass

    def get_amy_stats(self, action: dict):
        pass

    def get_one_life_stats(self, action: dict):
        pass
