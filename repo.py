import sqlite3
import json


class Repo:
    def __init__(self):
        self.database = SQLiteDB()

    def get_pet_links(self, payload: dict) -> dict:
        pet = payload["pet"]

        query = "SELECT title, link from pet_links WHERE pet=?"
        params = (pet,)

        all_links = self.database.fetch_db(query, params, True)
        loaded_links = {}

        for pet in all_links:
            title = pet[0]
            link = pet[1]

            loaded_links[title] = link

        return loaded_links

    def read_config_row(self, action: dict) -> dict:
        payload = action["payload"]
        key = payload["key"]

        query = "SELECT data FROM configs WHERE config=?"
        params = (key,)

        config_json = self.database.fetch_db(query, params, False)[0]
        config_dict = json.loads(config_json)

        return config_dict

    def set_config_row(self, action: dict):
        payload = action["payload"]
        key = payload["key"]
        value = payload["value"]

        query = "UPDATE configs SET data=? WHERE config=?"

        stringified_value = json.dumps(value)

        params = (stringified_value, key)

        self.database.set_db(query, params)

    def add_pet(self, action: dict):
        payload = action["payload"]
        pet_data = payload["pet_data"]

        query = "INSERT INTO pet_links VALUES (?, ?, ?)"

        try:
            self.database.set_db(query, pet_data)
        except sqlite3.IntegrityError as e:
            print(e)

    def update_permission(self, action: dict):
        payload = action["payload"]
        updated_player = payload["updated_player"]
        level = payload["level"]

        level = int(level)

        if not -2 <= level <= 3:
            return

        query = """
                    INSERT INTO permissions(user, level) VALUES(?1, ?2)
                    ON CONFLICT(user) DO UPDATE SET level=?2
                """
        params = (updated_player, level)
        self.database.set_db(query, params)

    def set_cheaters_permissions(self, action: dict):
        payload = action["payload"]
        player_list = payload["player_list"]

        cur = self.database.con.cursor()

        query = """
                        INSERT INTO permissions(user, level) VALUES(?1, ?2)
                        ON CONFLICT(user) DO UPDATE SET level=?2
                    """
        for player in player_list:
            params = (player, -2)
            cur.execute(query, params)

        self.database.con.commit()

    def get_pet_link(self, payload: dict):
        pet_name = payload.get("pet", None)
        if pet_name is not None:
            query = "SELECT title, pet, link FROM pet_links WHERE pet=? ORDER BY RANDOM() LIMIT 1;"
            params = (pet_name.lower(),)
        else:
            query = "SELECT title, pet, link FROM pet_links ORDER BY RANDOM() LIMIT 1;"
            params = tuple()

        pet_link = self.database.fetch_db(query, params, False)

        return pet_link

    def get_pet_link_by_title(self, payload: dict):
        title = payload["title"]

        query = "SELECT title, pet, link FROM pet_links WHERE title=? LIMIT 1;"
        params = (title.lower(),)

        pet_link = self.database.fetch_db(query, params, False)

        return pet_link

    def get_pet_stats(self):
        query = "SELECT pet, GROUP_CONCAT(title) FROM pet_links GROUP BY pet"
        params = tuple()
        pet_data = self.database.fetch_db(query, params, True)

        return pet_data

    def fetch_db(self, action: dict):
        return self.database.fetch_db(action["query"], action["params"], action["many"])


class SQLiteDB:
    def __init__(self):
        self.con = sqlite3.connect("configs.db")

    def fetch_db(self, query: str, params: tuple, many: bool):
        cur = self.con.cursor()

        if params:
            res = cur.execute(query, params)
        else:
            res = cur.execute(query)

        if many:
            data = res.fetchall()
        else:
            data = res.fetchone()

        return data

    def set_db(self, query: str, params: tuple):
        cur = self.con.cursor()

        cur.execute(query, params)

        self.con.commit()
