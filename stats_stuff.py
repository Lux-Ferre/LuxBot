import random

from multiprocessing.queues import Queue
from datetime import datetime

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
            self.update_one_life(yell_text)

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

    def handle_dynamic_command(self, message_data: dict):
        message_text = message_data["message"]
        player = message_data["player"]

        if player["perm_level"] < 0:
            print(f"{player['username']}[{player['perm_level']} attempted to use dynamic command.")
            return

        if message_text[0] == "!":
            return

        dynamic_command_triggers = ["chat stat", "gimme", "fetch", "look up", "statistic"]

        trigger_found = False

        if "luxbot" in message_text.lower():
            for trigger in dynamic_command_triggers:
                if trigger in message_text.lower():
                    trigger_found = True

        if not trigger_found:
            return

        required_value = self.get_dynamic_request_type(message_text)

        if required_value is None:
            return

        if "day" in message_text:
            time_frame = 1
        elif "hour" in message_text:
            time_frame = 2
        else:
            time_frame = 0

        response = self.generate_dynamic_request_response(player["username"], required_value, time_frame)

        print(response)

    @staticmethod
    def get_dynamic_request_type(message_text: str) -> str | None:
        required_value = None

        if "amy" in message_text:
            if "suck" in message_text:
                required_value = "amy_sucks"
            elif "noob" in message_text:
                required_value = "amy_noobs"
            elif "spoken" in message_text or "messages" in message_text:
                required_value = "amy_total"
        elif "noob" in message_text:
            required_value = "total_noobs"
        elif "other bot" in message_text:
            required_value = "botofnades_requests"
        elif "blood diamond" in message_text:
            required_value = "blood_diamonds_found"
        elif "diamond" in message_text:
            required_value = "diamonds_found"
        elif "blood gem goblin" in message_text:
            required_value = "blood_goblin_encounters"
        elif "gem goblin" in message_text:
            required_value = "gem_goblin_encounters"
        elif "server message" in message_text:
            required_value = "total_yells"
        elif "elite" in message_text:
            required_value = "elite_achievements"
        elif "sigils" in message_text:
            required_value = "sigils_found"
        elif "asked you" in message_text:
            required_value = "luxbot_requests"
        elif "max" in message_text:
            required_value = "max_levels"
        elif "messages" in message_text:
            required_value = "total_messages"
        elif "playtime" in message_text:
            required_value = "playtime"
        elif "hevent" in message_text:
            required_value = "hevent"
        elif "zombo" in message_text:
            required_value = "zombo"

        return required_value

    def generate_dynamic_request_response(self, player: str, required_value: str, time_frame: int) -> str:
        chat_stats = self.db.read_config_row({"key": "chat_stats"})

        if required_value == "playtime":
            diamonds = chat_stats["diamonds_found"]
            blood_diamonds = chat_stats["blood_diamonds_found"]

            est_by_diamonds = (diamonds * 1000000) / 60 / 60
            est_by_blood_diamonds = blood_diamonds * 25000000 / 60 / 60
            requested_value = round((est_by_blood_diamonds + est_by_diamonds) / 2)
        else:
            requested_value = chat_stats[required_value]

        if required_value == "hevent":
            start_date = "23/10/23 17:00"
        elif required_value == "zombo":
            start_date = "25/10/23 11:00"
        else:
            start_date = chat_stats["start_date"]

        start_datetime = datetime.strptime(start_date, "%d/%m/%y %H:%M")
        delta = datetime.now() - start_datetime
        total_time = round(delta.total_seconds())

        request_per_time = self.__per_time(total_time, requested_value)

        match time_frame:
            case 1:
                response_timeframe = "every day"
            case 2:
                response_timeframe = "every hour"
            case _:
                if required_value == "hevent":
                    response_timeframe = "since 17:00 23/10/2023 BST"
                elif required_value == "zombo":
                    response_timeframe = "since 11:00 25/10/2023 BST"
                else:
                    response_timeframe = "since 09/08/2023"

        response_value = f"{request_per_time[time_frame]} {response_timeframe}"

        response_patterns = [
            f"Here's the number you wanted {player.capitalize()}: {response_value}. Get it yourself next time.",
            f"Ugh. Fine. Here: {response_value}.",
            f"You're so lazy! Here: {response_value}.",
            f"-.- {response_value}",
            f"*sigh* {response_value}",
            f"Damn slave driver... {response_value}...",
        ]

        return random.choice(response_patterns)

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

    def update_one_life(self, yell_text: str):
        mob_name = yell_text.split("died to a ")[1].split(" and lost")[0]

        current_stats = self.db.read_config_row({"key": "one_life_killers"})

        if mob_name not in current_stats:
            current_stats[mob_name] = 1
        else:
            current_stats[mob_name] += 1

        update_data = {
            "key": "one_life_killers",
            "value": current_stats
        }
        self.db.set_config_row(update_data)

        if mob_name == "spider":
            spider_kills = current_stats["spider"]

            custom_data = {
                "player": "a spider",
                "plugin": "spiderTaunt",
                "command": "spiderKill",
                "payload": str(spider_kills),
            }

            send_action = Utils.gen_send_action("custom", custom_data)

            self.p_q.put(send_action)

    def get_specific_stat(self, action: dict):
        pass

    def get_all_stats(self, action: dict):
        pass

    def get_amy_stats(self, action: dict):
        pass

    def get_one_life_stats(self, action: dict):
        pass
