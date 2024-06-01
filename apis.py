import os
import queue
import discord
import aiohttp
import asyncio
import requests

from multiprocessing.queues import Queue

from utils import Utils


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
            "paste": {
                "target": self.paste,
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
            "DISCORD_CHAT_WEBHOOK_URL": "",
            "DISCORD_EVENT_WEBHOOK_URL": "",
            "IP_DATA_KEY": "",
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
        hook_url = self.env_consts["DISCORD_CHAT_WEBHOOK_URL"]

        message = message.replace("@mods", "<@&291724449340719104>", 1)
        allowed = discord.AllowedMentions(everyone=False, users=False,
                                          roles=[discord.Object(id="291724449340719104", type=discord.Role)])

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(hook_url, session=session)
            await webhook.send(content=message, allowed_mentions=allowed)

    async def event_webhook(self, action: dict):
        message = action["payload"]
        hook_url = self.env_consts["DISCORD_EVENT_WEBHOOK_URL"]

        allowed = discord.AllowedMentions(everyone=False, users=False,
                                          roles=[discord.Object(id="1142985685184282705", type=discord.Role)])

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(hook_url, session=session)
            await webhook.send(content=message, allowed_mentions=allowed)

    async def paste(self, action: dict):
        paste_string = action["payload"]["data"]
        paste_title = action["payload"]["title"]
        message_wrapper = action["payload"]["wrapper"]
        api_key = self.env_consts["IP_DATA_KEY"]

        body = {
            "paste": paste_string,
            "title": paste_title
        }

        headers = {
            'accept': 'application/json',
            'X-API-Key': api_key,
            'Content-Type': 'application/json',
        }

        response = requests.post('https://data.idle-pixel.com/api/paste/', headers=headers, json=body)
        paste_url = f"https://data.idle-pixel.com/api/paste/?paste_id={response.text[1:-1]}"
        reply_message = message_wrapper.replace("{{url}}", paste_url)

        reply_data = {
            "player": action["payload"]["player"],
            "payload": reply_message,
            "command": action["payload"]["command"]
        }

        send_action = Utils.gen_send_action("chat", reply_data)

        if send_action:
            self.p_q.put(send_action)
        else:
            print("stats_stuff error: Invalid source for send.")

    def run(self):
        while True:
            try:
                new_action = self.api_queue.get(False)
                asyncio.run(self.dispatch(new_action))
            except queue.Empty:
                pass
