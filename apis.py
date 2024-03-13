import os
import queue
import discord
import aiohttp
import asyncio

from multiprocessing.queues import Queue


class APIs:
    def __init__(self, p_q: Queue, api_queue: Queue):
        self.env_consts = self.get_env_consts()
        self.p_q = p_q
        self.api_queue = api_queue
        self.dispatch_map = {
            "chat_mirror_webhook": {
                "target": self.chat_mirror_webhook,
            },
            "event_webhook": {
                "target": self.event_webhook,
            },
        }

    def get_env_var(self, env_var: str) -> str:
        """Return environment variable of key ``env_var``. Will stop application if not found."""
        try:
            return os.environ[env_var]
        except KeyError:
            print(f"Missing environment variable: {env_var}")
            raise

    def get_env_consts(self) -> dict:
        """Return dict containing all required environment variables at application launch."""
        env_const_dict = {
            "DISCORD_TEST_WEBHOOK_URL": "",
        }

        for key in env_const_dict:
            env_const_dict[key] = self.get_env_var(key)

        return env_const_dict

    async def dispatch(self, action: dict):
        action_target = self.dispatch_map.get(action["action"], None)

        if action_target is None:
            print(f"API dispatch error: No handler for {action['action']}")
            return

        await action_target["target"](action)

    async def chat_mirror_webhook(self, action: dict):
        message = action["payload"]
        hook_url = self.env_consts["DISCORD_TEST_WEBHOOK_URL"]

        message = message.replace("@mods", "<@&291724449340719104>", 1)
        allowed = discord.AllowedMentions(everyone=False, users=False,
                                          roles=[discord.Object(id="291724449340719104", type=discord.Role)])

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(hook_url, session=session)
            await webhook.send(content=message, allowed_mentions=allowed)

    async def event_webhook(self, action: dict):
        message = action["payload"]
        hook_url = self.env_consts["DISCORD_TEST_WEBHOOK_URL"]

        allowed = discord.AllowedMentions(everyone=False, users=False,
                                          roles=[discord.Object(id="1142985685184282705", type=discord.Role)])

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(hook_url, session=session)
            await webhook.send(content=message, allowed_mentions=allowed)

    def run(self):
        while True:
            try:
                new_action = self.api_queue.get(False)
                asyncio.run(self.dispatch(new_action))
            except queue.Empty:
                pass


""" Temporary copy of TCG scraper to use as base
import copy
import requests

from bs4 import BeautifulSoup
from datetime import datetime


def get_card_data() -> list:
    page = requests.get("https://idle-pixel.com/hiscores/tcg")
    soup = BeautifulSoup(page.text, 'html.parser')
    table = soup.find("table", {"width": "50%"})

    card_data = []

    for row in table.findAll("tr"):
        cells = row.findAll("td")

        if len(cells) == 6:
            owner = cells[0].find(string=True)
            card = cells[1].find(string=True)
            image = cells[2].find(string=True)
            rarity = cells[3].find(string=True).title()

            holo_scrape = cells[5].find(string=True)
            if holo_scrape:
                holo = True
            else:
                holo = False

            stripped_date = cells[4].find(string=True).replace(".", "").replace(",", "").strip()
            if stripped_date[-6] != ":":
                stripped_date = f"{stripped_date[:-3]}:00 {stripped_date[-2:]}"

            date = datetime.strptime(stripped_date, "%B %d %Y %I:%M %p")

            card_data.append({
                "owner": owner,
                "card": card,
                "image": image,
                "rarity": rarity,
                "date": date,
                "holo": holo
            })

    return card_data


def parse_card_data(card_data):
    parsed_data = {}

    for card_find in card_data:
        card_name = card_find["card"]

        if card_find["card"] in parsed_data:
            parsed_data[card_name]["owners"].append(card_find["owner"])

            if parsed_data[card_name]["first_find_date"] > card_find["date"]:
                parsed_data[card_name]["first_find_date"] = card_find["date"]
                parsed_data[card_name]["first_find_player"] = card_find["owner"]

            if card_find["holo"]:
                parsed_data[card_name]["holo_owners"].append(card_find["owner"])
                if parsed_data[card_name]["holo"]:
                    if parsed_data[card_name]["first_holo_date"] > card_find["date"]:
                        parsed_data[card_name]["first_holo_date"] = card_find["date"]
                        parsed_data[card_name]["first_holo_player"] = card_find["owner"]
                else:
                    parsed_data[card_name]["first_holo_date"] = card_find["date"]
                    parsed_data[card_name]["first_holo_player"] = card_find["owner"]

            if not parsed_data[card_name]["holo"]:
                parsed_data[card_name]["holo"] = card_find["holo"]

        else:
            parsed_data[card_name] = {
                "display": card_name.title(),
                "rarity": card_find["rarity"],
                "first_find_date": card_find["date"],
                "first_find_player": card_find["owner"],
                "holo": card_find["holo"],
                "owners": [card_find["owner"]],
                "holo_owners": [],
            }

            if card_find["holo"]:
                parsed_data[card_name]["first_holo_date"] = card_find["date"]
                parsed_data[card_name]["first_holo_player"] = card_find["owner"]
                parsed_data[card_name]["holo_owners"] = [card_find["owner"]]

    return dict(sorted(parsed_data.items()))


def get_full_card_data():
    response = requests.get('https://idle-pixel.com/get-tcg-info/')

    return response.json()


def get_full_card_list(card_data):
    card_list = []
    for card in card_data.values():
        card_list.append(card["label"].title())

    return card_list


def parse_full_list(card_data):
    parsed_full_list = {}

    for var, card in card_data.items():
        label = card["label"]
        category = card["description_title"].title()
        description = card["description"]
        bg_css = card["background_css"]
        bdr_css = card["border_css"]
        rarity = card["rarity"].title()

        if var == "tcg_pine_logs":
            label = "PINE LOGS"
        elif var == "tcg_shark_icon":
            label = "SHARK MOB"

        parsed_full_list[label] = {
            "var": var,
            "category": category,
            "description": description,
            "bg_css": bg_css,
            "bdr_css": bdr_css,
            "rarity": rarity
        }

    return dict(sorted(parsed_full_list.items()))


def pretty_format_cards(parsed_cards, number_found, total_number):
    output_string = f"Players have found {number_found}/{total_number} of the cards!\n\n"

    for card_name, card in parsed_cards.items():
        display = card.get("display", card_name.title())
        rarity = card["rarity"]
        holo = card.get("holo", "False")
        found_date = card.get("first_find_date", "None")
        first_owner = card.get("first_find_player", "None")
        holo_date = card.get("first_holo_date", "None")
        holo_player = card.get("first_holo_player", "None")
        owners = set(card.get("owners", []))
        category = card["category"]

        if owners is not None:
            owners = sorted(owners)
            owner_string = ""
            for owner in owners:
                owner_string += f"{owner.title()}, "

            owner_string = owner_string[:-2]
        else:
            owner_string = "None"

        new_card = f"{display}:\n\tCategory: {category}\n\tRarity: {rarity}\n\tHolo Found: {holo}\n\tFirst Holo Found: {holo_date}\n\tOldest Holo Owner: {holo_player}\n\tFirst Found Date: {found_date}\n\tOldest Card Owner: {first_owner}\n\tOwners: {owner_string}\n\n"
        output_string += new_card

    with open("card_info.txt", mode="w+", encoding="utf-8") as my_file:
        my_file.write(output_string)


def merge_data_sets(api_data: dict, score_data: dict):
    for api_key, api_value in api_data.items():
        if api_key in score_data:
            api_data[api_key] = api_value | score_data[api_key]

    return api_data


def sort_by_owner(parsed_cards):
    cards = copy.deepcopy(parsed_cards)
    player_dict = {}

    for card_name, card in cards.items():
        for owner in card["owners"]:
            if owner in card["holo_owners"]:
                holo = "ᴴ"
                card["holo_owners"].remove(owner)
            else:
                holo = ""
            if owner in player_dict:
                player_dict[owner].append(f"{card_name}{holo}")
            else:
                player_dict[owner] = [f"{card_name}{holo}"]

    return player_dict


def pretty_print_owners(owners):
    owners = dict(sorted(owners.items(), key=lambda x: len(x[1]), reverse=True))
    output_string = ""

    for owner, collection in owners.items():
        size = len(collection)
        owner_string = f"{owner.title()}[{size}]:\n\t"
        for card in collection:
            owner_string += f"{card.title()}, "
        owner_string = owner_string[:-2] + "\n\n"

        output_string += owner_string

    with open("owner_collections.txt", mode="w+", encoding="utf-8") as my_file:
        my_file.write(output_string)


def main():
    scores_card_data = get_card_data()
    parsed_scores_cards = parse_card_data(scores_card_data)

    api_card_data = get_full_card_data()
    parsed_api_cards = parse_full_list(api_card_data)

    merged_card_data = merge_data_sets(parsed_api_cards, parsed_scores_cards)

    number_found = len(parsed_scores_cards)
    total_number = len(merged_card_data)

    pretty_format_cards(merged_card_data, number_found, total_number)

    collections = sort_by_owner(parsed_scores_cards)
    pretty_print_owners(collections)
"""