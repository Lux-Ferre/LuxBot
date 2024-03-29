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

    def read_config_row(self, payload: dict) -> dict:
        key = payload["key"]

        query = "SELECT data FROM configs WHERE config=?"
        params = (key,)

        config_json = self.database.fetch_db(query, params, False)[0]
        config_dict = json.loads(config_json)

        return config_dict

    def set_config_row(self, payload: dict):
        key = payload["key"]
        value = payload["value"]

        query = "UPDATE configs SET data=? WHERE config=?"

        stringified_value = json.dumps(value)

        params = (stringified_value, key)

        self.database.set_db(query, params)

    def add_pet(self, pet_data: tuple):
        query = "INSERT INTO pet_links VALUES (?, ?, ?)"

        try:
            self.database.set_db(query, pet_data)
            return {"has_error": False, "error_type": None}
        except sqlite3.IntegrityError as e:
            print(e)
            return {"has_error": True, "error_type": "integrity"}

    def update_permission(self, payload: dict):
        updated_player = payload["updated_player"]
        level = payload["level"]

        try:
            level = int(level)
        except ValueError:
            print("Permission level must be a number between -2 and 3")
            return

        if not -2 <= level <= 3:
            print("Invalid new permission level.")
            return

        query = """
                    INSERT INTO permissions(user, level) VALUES(?1, ?2)
                    ON CONFLICT(user) DO UPDATE SET level=?2
                """
        params = (updated_player, level)
        self.database.set_db(query, params)

    def set_cheaters_permissions(self, payload: dict):
        cheater_list = payload["cheater_list"]

        cur = self.database.con.cursor()

        query = """
                        INSERT INTO permissions(user, level) VALUES(?1, ?2)
                        ON CONFLICT(user) DO UPDATE SET level=?2
                    """
        for cheater in cheater_list:
            params = (cheater, -2)
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

    def permission_level(self, payload: dict):
        player = payload["player"]

        query = "SELECT level FROM permissions WHERE user=?"
        params = (player,)

        level = self.database.fetch_db(query, params, False)
        if level is None:
            return 0
        else:
            return level[0]


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
