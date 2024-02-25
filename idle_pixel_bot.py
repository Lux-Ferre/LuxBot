import asyncio
import os
import queue
import websocket
import rel
import ssl
import traceback

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from datetime import datetime
from multiprocessing.queues import Queue

from utils import RepeatTimer


class Game:
    def __init__(self, p_q: Queue, game_queue: Queue):
        self.env_consts = {}
        self.game_ws = None
        self.p_q = p_q
        self.game_queue = game_queue
        self.game_vars = {}

        self.dispatch_map = {
            "set_items": {
                "target": self.set_items,
            },
            "print_items": {
                "target": self.print_items,
            },
            "send_ws_message": {
                "target": self.send_ws_message
            }
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
            "IP_USERNAME": "",
            "IP_PASSWORD": "",
        }

        for key in env_const_dict:
            env_const_dict[key] = self.get_env_var(key)

        return env_const_dict

    def check_queue(self):
        try:
            new_action = self.game_queue.get(False)
            self.dispatch(new_action)
        except queue.Empty:
            pass

    async def get_signature(self) -> str:
        """
        Uses a Playwright headless browser to authenticate login.

        User authentication is done via HTTP, the server sends an authentication signature to the client which is then
        sent as the first frame over the websocket.

        A browser is used to comply with CORS security measures.

        :return: Authentication signature
        :rtype: str
        """
        async with async_playwright() as p:
            browser_type = p.chromium
            browser = await browser_type.launch_persistent_context("persistent_context")
            page = await browser.new_page()

            await page.goto("https://idle-pixel.com/login/")
            await page.locator('[id=id_username]').fill(self.env_consts["IP_USERNAME"])
            await page.locator('[id=id_password]').fill(self.env_consts["IP_PASSWORD"])
            await page.locator("[id=login-submit-button]").click()

            page_content = await page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            script_tag = soup.find("script").text

            sig_plus_wrap = script_tag.split(";", 1)[0]

            signature = sig_plus_wrap.split("'")[1]

            return signature

    def on_ws_message(self, ws, raw_message: str):
        """
        Primary handler for received websocket frames.

        :param ws: websocket
        :param raw_message: String containing websocket data
        :type raw_message: str
        """

        development_mode = False

        if development_mode:
            self.log_ws_message(raw_message, True)

        split_message = raw_message.split("=", 1)
        payload = None
        if len(split_message) > 1:
            payload = split_message[1]

        current_time = datetime.now()

        message_data = {
            "type": split_message[0],
            "payload": payload,
            "time": current_time,
        }

        action = {
            "target": "ws_handlers",
            "action": "dispatch",
            "payload": message_data,
            "source": "game",
        }

        self.p_q.put(action)

    def on_ws_error(self, ws, error):
        """
        Top level error handler.

        If websocket connection drops, will print a retrying message to notify before ``rel`` retries.
        Otherwise, prints timestamp, error, and traceback.

        :param ws: websocket
        :param error: Exception object
        """

        if isinstance(error, websocket.WebSocketConnectionClosedException):
            print("Connection closed. Retrying...")
        else:
            print(datetime.now().strftime("%d/%m/%Y , %H:%M:%S"))
            print(error)
            traceback.print_tb(error.__traceback__)

    def on_ws_close(self, ws, close_status_code, close_msg):
        """Called when websocket is closed by server."""
        print("### closed ###")

    def on_ws_open(self, ws):
        """
        Called when websocket opens.

        Acquires authentication signature then sends it as first frame over websocket.

        :param ws: websocket
        """
        print("Opened connection.")
        print("Acquiring signature...")
        signature = asyncio.run(self.get_signature())
        print("Signature acquired.")
        print("Logging in...")
        self.send_ws_message({"payload": f"LOGIN={signature}"})

    def log_ws_message(self, raw_message: str, received: bool):
        message_data = {
            "time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
            "length": len(raw_message),
            "message": raw_message,
            "received": received,
        }

        direction_indicator = "↓" if received else "↑"

        formatted_output = f"{direction_indicator}[{message_data['time']}] {message_data['message']}"

        print(formatted_output)

    def send_ws_message(self, action: dict):
        message = action["payload"]

        self.log_ws_message(message, False)
        self.game_ws.send(message)

    def dispatch(self, action: dict):
        action_target = self.dispatch_map.get(action["action"], None)

        if action_target is None:
            print(f"Game dispatch error: No handler for {action['action']}")
            return

        action_target["target"](action)

    def set_items(self, action: dict):
        new_items = action["payload"]
        self.game_vars.update(new_items)

    def print_items(self, action: dict):
        print(self.game_vars)

    def run(self):
        self.env_consts = self.get_env_consts()

        queue_timer = RepeatTimer(0.1, self.check_queue)
        queue_timer.start()

        websocket.enableTrace(False)
        self.game_ws = websocket.WebSocketApp("wss://server1.idle-pixel.com",
                                              on_open=self.on_ws_open,
                                              on_message=self.on_ws_message,
                                              on_error=self.on_ws_error,
                                              on_close=self.on_ws_close,
                                              )

        self.game_ws.run_forever(dispatcher=rel,
                                 reconnect=120,
                                 sslopt={
                                         "cert_reqs": ssl.CERT_NONE,
                                 })  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly, no SSL cert
        rel.dispatch()
