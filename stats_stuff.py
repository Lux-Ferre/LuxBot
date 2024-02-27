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
            "handle_dynamic_command": {
                "target": self.handle_dynamic_command
            },
            "update_one_life": {
                "target": self.update_one_life
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
        pass

    def handle_yell(self, action: dict):
        pass

    def handle_dynamic_command(self, action: dict):
        pass

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
