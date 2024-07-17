import requests
import json
import os

from multiprocessing.queues import Queue

from repo import Repo
from utils import Utils


class Data:
    """
    Handler for interacting with the data.idle-pixel.com/api API
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
            "deaths_per_user": {
                "target": self.get_deaths_per_user,
            },
            "levels_lost": {
                "target": self.get_levels_lost,
            },
        }
        self.api_uri = "https://data.idle-pixel.com/api"
        self.api_key = os.environ["IP_DATA_KEY"]

    def dispatch(self, action: dict):
        """
        Method for dispatching actions from the primary handler to Admin methods
        :param action: Action dict with format:
            {target: "admin", action: "dispatch map key", payload: {payload}, source: "source"}
        :type action: dict
        """

        target_dict = self.dispatch_map.get(action["action"], None)

        if target_dict is None:
            print(f"Data dispatch error: No handler for {action['action']}")
            return

        target_dict["target"](action)

    def api_get(self, endpoint: str, queries: dict = None):
        url = f"{self.api_uri}{endpoint}?"

        if queries is not None:
            for key, value in queries.items():
                url += f"{key}={value}&"

        headers = {
            'accept': 'application/json',
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
        }

        response = requests.get(url, headers=headers)

        return response.json()

    def get_deaths_per_user(self, action: dict):
        message = action["payload"]
        parsed_command = message["parsed_command"]
        player = message["player"]
        request_source = action["source"]

        response = self.api_get("/onelife/user-deaths")

        output = ""

        for key, value in response.items():
            output += f"{key}: {value}\n"

        title = "One Life Deaths per User: {{ creation_local_datetime }}"

        new_action = {
            'target': 'api',
            'action': 'paste',
            'payload': {
                "data": output,
                "title": title,
                "wrapper": f"{player['username'].capitalize()}, here are the stats: " + "{{url}}",
                "player": player["username"],
                "command": "deaths_per_user"
            },
            'source': 'chat'
        }

        self.p_q.put(new_action)

    def get_levels_lost(self, action: dict):
        message = action["payload"]
        parsed_command = message["parsed_command"]
        player = message["player"]
        request_source = action["source"]

        response = self.api_get("/onelife/levels-lost")

        output = ""

        for key, value in response.items():
            output += f"{key}: {value}\n"

        title = "One Life Levels Lost per Enemy: {{ creation_local_datetime }}"

        new_action = {
            'target': 'api',
            'action': 'paste',
            'payload': {
                "data": output,
                "title": title,
                "wrapper": f"{player['username'].capitalize()}, here are the stats: " + "{{url}}",
                "player": player["username"],
                "command": "levels_lost"
            },
            'source': 'chat'
        }

        self.p_q.put(new_action)
