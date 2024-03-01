from multiprocessing.queues import Queue
from collections import deque
from datetime import datetime, timedelta, timezone

from repo import Repo
from utils import Utils


class Integrations:
    def __init__(self, p_q: Queue, db: Repo):
        self.p_q = p_q
        self.db = db
        self.dispatch_map = {
            "chat_hist_request": {
                "target": self.chat_hist_request
            },
            "log_chat_history": {
                "target": self.log_chat_history
            },
            "mirror_chat_to_discord": {
                "target": self.mirror_chat_to_discord
            },
            "broadcast_event_start": {
                "target": self.broadcast_event_start
            },
            "broadcast_event_end": {
                "target": self.broadcast_event_end
            },
        }
        self.chat_history = deque([], 5)

    def dispatch(self, action: dict):
        target_dict = self.dispatch_map.get(action["action"], None)

        if target_dict is None:
            print(f"Integration dispatch error: No handler for {action['action']}")
            return

        target_dict["target"](action)

    def log_chat_history(self, action):
        chat_data = action["payload"]["payload"]
        self.chat_history.append(chat_data)

    def chat_hist_request(self, action: dict):
        player = action["payload"]["player"]
        perm_level = player["perm_level"]
        command = action["payload"]["command"]

        if command != "logon":
            return

        if perm_level < 0:
            return

        chat_history = self.chat_history

        actions = []

        for message in chat_history:
            reply_data = {
                "player": player["username"],
                "plugin": "chathist",
                "command": "addMessage",
                "payload": message,
            }

            send_action = Utils.gen_send_action("custom", reply_data)
            actions.append(send_action)

        reply_data = {
            "player": player["username"],
            "plugin": "chathist",
            "command": "endstream",
            "payload": "none",
        }

        send_action = Utils.gen_send_action("custom", reply_data)
        actions.append(send_action)

        for new_action in actions:
            self.p_q.put(new_action)

    def mirror_chat_to_discord(self, action: dict):
        message_data = action["payload"]
        if message_data["has_slur"]:
            return

        player = message_data["player"]
        message = message_data["message"]
        message_time = message_data["time"]

        timestamp = int(message_time.timestamp())
        timestamp_string = f"<t:{timestamp}:t>"

        formatted_chat = f'*[{timestamp_string}]* **{player["username"]}:** {message} '

        new_action = {
            'target': 'api',
            'action': 'chat_mirror_webhook',
            'payload': formatted_chat,
            'source': 'integration'
        }

        self.p_q.put(new_action)

    def broadcast_event_start(self, action: dict):
        start_timer = action["payload"]["start_timer"]
        event_type = action["payload"]["event_type"]

        current_time = datetime.now(timezone.utc)
        time_delta = timedelta(seconds=start_timer)

        event_start_object = current_time + time_delta
        timestamp = int(event_start_object.timestamp())
        event_start_string = f"<t:{timestamp}:f>"

        discord_declaration = f"<@&1142985685184282705>, A {event_type} event will start in {start_timer} seconds! ({event_start_string})"

        new_action = {
            'target': 'api',
            'action': 'event_webhook',
            'payload': discord_declaration,
            'source': 'integration'
        }

        self.p_q.put(new_action)

    def broadcast_event_end(self, action: dict):
        event_type = action["payload"]["event_type"]
        sorted_scores = action["payload"]["sorted_scores"]

        formatted_scores = f"The last event was a {event_type} event. The final scores were: \n"

        for rank, username in enumerate(sorted_scores):
            new_line = f"{rank + 1}: {username} - {sorted_scores[username]}\n"
            if len(formatted_scores) + len(new_line) < 2000:
                formatted_scores += new_line
            else:
                break

        new_action = {
            'target': 'api',
            'action': 'event_webhook',
            'payload': formatted_scores,
            'source': 'integration'
        }

        self.p_q.put(new_action)
