import os
import requests

from threading import Timer


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


class Utils:
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

    @staticmethod
    def gen_mute_action(target, length, reason, is_ip):
        mute_data = f"MUTE={target}~{length}~{reason}~{is_ip}"

        mute_action = {
            "target": "game",
            "action": "send_ws_message",
            "payload": mute_data,
            "source": "custom",
        }

        return mute_action
