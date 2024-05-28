import requests
import json

from multiprocessing.queues import Queue

from repo import Repo
from utils import Utils


class Admin:
    """
    Handler for misc, administrative, and meta tasks. eg database changes, or resetting the app
    """
    def __init__(self, p_q: Queue, db: Repo):
        """
        :param p_q: Primary queue. For communicating messages up to the primary handler
        :type p_q: multiprocessing.queues.Queue
        :param db: Repo instance for accessing the database
        :type db: Repo
        """
        self.p_q = p_q
        self.db = db
        # Map is a dict of dicts for consistency between handlers, and to allow for future expansion.
        self.dispatch_map = {
            "speak": {
                "target": self.speak
            },
            "update_cheaters": {
                "target": self.update_cheaters
            },
            "update_permissions": {
                "target": self.update_permissions
            },
            "add_stat": {
                "target": self.add_stat
            },
            "generic_ws": {
                "target": self.generic
            },
            "close_connection": {
                "target": self.close_connection
            },
            "test": {
                "target": self.test_stuff
            }
        }

    def dispatch(self, action: dict):
        """
        Method for dispatching actions from the primary handler to Admin methods
        :param action: Action dict with format:
            {target: "admin", action: "dispatch map key", payload: {payload}, source: "source"}
        :type action: dict
        """

        target_dict = self.dispatch_map.get(action["action"], None)

        if target_dict is None:
            print(f"Admin dispatch error: No handler for {action['action']}")
            return

        target_dict["target"](action)

    def speak(self, action: dict):
        """
        Sends a chat message. Used when manually sending a chat message (eg via Interactor), not automated replies.
        :param action: Action dict with format:
            {
                payload: {
                    player: {
                        username: "username requesting the command",
                        ...
                    },
                    parsed_command: {
                        payload: "message to be relayed",
                        ...
                    },
                    ...
                }
            }
        """
        message = action["payload"]
        parsed_command = message["parsed_command"]
        player = message["player"]

        reply_string = parsed_command["payload"]

        reply_data = {
            "player": player["username"],
            "command": "speak",
            "payload": reply_string,
        }

        send_action = Utils.gen_send_action("chat", reply_data)

        if send_action:
            self.p_q.put(send_action)
        else:
            print("admin_stuff error: Invalid source for send.")

    def update_cheaters(self, action: dict):
        """
        Updates database permissions to give -2 (blacklisted for cheating) to users from Nades's dataset
        :param action: (Unused) Action dict
        :type action: dict
        """
        url = 'https://raw.githubusercontent.com/GodofNades/idle-pixel/main/AltTraders.json'
        resp = requests.get(url)
        data = json.loads(resp.text)

        cheater_list = []
        for data_point in data:
            cheater_list.append(data_point["name"])

        self.db.set_cheaters_permissions({"cheater_list": cheater_list})

    def update_permissions(self, action: dict):
        """
        Updates a user's permission level in the permissions db.
        :param action: Action dict with format:
            {
                payload: {
                    parsed_command: {
                        payload: "player;level",
                        ...
                    },
                    ...
                },
                ...
            }
        :type action: dict
        """
        message = action["payload"]
        parsed_command = message["parsed_command"]

        content = parsed_command["payload"]
        split_command = content.split(";")
        if len(split_command) != 2:
            print("Invalid syntax. Must be of form 'permissions:player;level'")
            return

        updated_player = split_command[0]
        level = split_command[1]

        update_data = {
            "updated_player": updated_player,
            "level": level
        }

        self.db.update_permission(update_data)

    def add_stat(self, action: dict):
        """
        Adds a new stat tracking datapoint to the chat_stats stored in the db.
        :param action: Action dict with format:
            {
                payload: {
                    parsed_command: {
                        payload: "new stat key",
                        ...
                    },
                    ...
                },
                ...
            }
        :type action: dict
        """
        message = action["payload"]
        parsed_command = message["parsed_command"]

        new_stat = parsed_command["payload"]

        current_stats = self.db.read_config_row({"key": "chat_stats"})
        if new_stat in current_stats:
            print(f"The value {new_stat} already exists!")
            return

        current_stats[new_stat] = 0

        update_data = {
            "key": "chat_stats",
            "value": current_stats
        }
        self.db.set_config_row(update_data)

    def generic(self, action: dict):
        """
        Used to send arbitrary websocket messages to the game server.
        :param action: Action dict with format:
            {
                payload: {
                    parsed_command: {
                        payload: "full ws message eg 'RFRESH_TCG_CLIENT'",
                        ...
                    },
                    ...
                },
                source: "source",
                ...
            }
        :type action: dict
        """
        message = action["payload"]
        parsed_command = message["parsed_command"]
        message_source = action["source"]

        ws_message = parsed_command["payload"]

        action = {
            "target": "game",
            "action": "send_ws_message",
            "payload": ws_message,
            "source": message_source,
        }

        self.p_q.put(action)

    def close_connection(self, action: dict):
        """
        Sends a close or restart instruction up to the primary handler.
        :param action: Action dict with format:
            {
                payload: {
                    parsed_command: {
                        payload: "close" OR "restart",
                        ...
                    },
                    ...
                },
                source: "source",
                ...
            }
        :type action: dict
        """
        message = action["payload"]
        parsed_command = message["parsed_command"]
        payload = parsed_command["payload"]
        message_source = action["source"]

        if payload == "close":
            action = {
                "target": "main",
                "action": "main_close",
                "payload": "",
                "source": message_source,
            }
        elif payload == "restart":
            action = {
                "target": "main",
                "action": "main_restart",
                "payload": "",
                "source": message_source,
            }
        else:
            action = None

        if action:
            self.p_q.put(action)

    def test_stuff(self, action: dict):
        """
        Sends pre-defined actions to primary handler when triggered, used for testing.
        :param action: (Unused) Action dict
        :type action: dict
        """
        actions = [
        ]

        if not actions:
            return

        for new_action in actions:
            self.p_q.put(new_action)
