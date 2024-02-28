from multiprocessing.queues import Queue
from datetime import datetime, timedelta, timezone

from repo import Repo
from utils import Utils


class Event:
    def __init__(self, p_q: Queue, db: Repo):
        self.p_q = p_q
        self.db = db
        self.dispatch_map = {
            "handle_event_progress": {
                "target": self.handle_event_progress
            },
            "handle_set_items": {
                "target": self.handle_set_items
            },
        }
        self.raw_event_scores = ""
        self.parsed_event_score = {}
        self.event_countdown_started = False
        self.current_event_start_timer = 0
        self.current_event_type = ""
        self.current_event_running_timer = 0

    def dispatch(self, action: dict):
        target_dict = self.dispatch_map.get(action["action"], None)

        if target_dict is None:
            print(f"Mod dispatch error: No handler for {action['action']}")
            return

        target_dict["target"](action)

    def handle_event_progress(self, action: dict):
        message = action["payload"]["payload"]
        self.raw_event_scores = message

    def handle_set_items(self, action: dict):
        parsed_items = action["payload"]

        new_data = {
            "current_event_start_timer": parsed_items.get("event_upcomming_timer", None),
            "current_event_type": parsed_items.get("event_name", None),
            "current_event_running_timer": parsed_items.get("event_active_timer", None),
        }

        for key, value in new_data.items():
            if value:
                setattr(self, key, value)

        self.update_event_status()

    def update_event_status(self):
        start_timer = self.current_event_start_timer
        running_timer = self.current_event_running_timer
        if start_timer > 0 and not self.event_countdown_started:
            self.start_event_countdown()
        elif running_timer < 0 and self.event_countdown_started:
            self.handle_event_end()

    def start_event_countdown(self):
        self.event_countdown_started = True
        start_timer = self.current_event_start_timer
        event_type = self.current_event_type

        current_time = datetime.now(timezone.utc)
        time_delta = timedelta(seconds=start_timer)

        event_start_object = current_time + time_delta
        timestamp = int(event_start_object.timestamp())
        event_start_string = f"<t:{timestamp}:f>"

        discord_declaration = f"<@&1142985685184282705>, A {event_type} event will start in {start_timer} seconds! ({event_start_string})"

        print(discord_declaration)

    def handle_event_end(self):
        self.event_countdown_started = False
        event_type = self.current_event_type

        raw_data = self.raw_event_scores

        parsed_scores = {}
        split_data = raw_data.split("~")
        for i in range(0, len(split_data), 2):
            parsed_scores[split_data[i]] = int(split_data[i + 1])

        sorted_scores = dict(sorted(parsed_scores.items(), key=lambda item: item[1], reverse=True))

        self.parsed_event_score = sorted_scores

        formatted_scores = f"The last event was a {event_type} event. The final scores were: \n"

        for rank, username in enumerate(sorted_scores):
            new_line = f"{rank + 1}: {username} - {sorted_scores[username]}\n"
            if len(formatted_scores) + len(new_line) < 2000:
                formatted_scores += new_line
            else:
                break

        print(formatted_scores)
