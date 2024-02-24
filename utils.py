import os
import requests

from threading import Timer


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class Utils:
    @staticmethod
    def dump_to_pastebin(paste_string: str, expiry: str) -> str:
        api_key = os.environ["PASTEBIN_API_KEY"]
        url = "https://pastebin.com/api/api_post.php"
        data = {
            "api_dev_key": api_key,
            "api_option": "paste",
            "api_paste_code": paste_string,
            "api_paste_expire_date": expiry
        }

        response = requests.post(url=url, data=data)

        return response.text

    @staticmethod
    def gen_send_action(target: str, reply_data: dict):
        send_action = None

        if target == "chat":
            send_action = {
                "target": "chat",
                "action": "send",
                "payload": reply_data,
                "source": "chat",
            }
        elif target == "custom":
            send_action = {
                "target": "custom",
                "action": "send",
                "payload": reply_data,
                "source": "chat",
            }

        return send_action
