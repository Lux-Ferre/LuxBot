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
        message = message.replace("@mods", "<@&291724449340719104>", 1)
        allowed = discord.AllowedMentions(everyone=False, users=False,
                                          roles=[discord.Object(id="291724449340719104", type=discord.Role)])

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(self.env_consts["DISCORD_TEST_WEBHOOK_URL"], session=session)
            await webhook.send(content=message, allowed_mentions=allowed)

    def run(self):
        while True:
            try:
                new_action = self.api_queue.get(False)
                asyncio.run(self.dispatch(new_action))
            except queue.Empty:
                pass
