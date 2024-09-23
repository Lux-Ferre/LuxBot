from typing import Self, Optional
from datetime import datetime, timezone
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


class Message:
    def __init__(self, target: str, action: str, payload: str, source: str, previous: Optional[Self] = None):
        """
        Object for transporting data and commands through the application.
        :param target: The module which the Message should be sent to.
        :param action: Which method withing the module the dispatcher should pass the message to.
        :param payload: The data for use by the target's action method.
        :param source: Where the Message has come from.
        :param previous: The instance of Message which was processed to create this one, or None when it's the root.
        """
        self.target = target
        self.action = action
        self.payload = payload
        self.source = source
        self.timestamp = datetime.now(timezone.utc)
        self.previous = previous

    def __str__(self) -> str:
        return (f"target: {self.target},\n" +
                f"action: {self.action},\n" +
                f"payload: {self.payload},\n" +
                f"source: {self.source},\n" +
                f"timestamp: {self.timestamp}\n" +
                f"previous: {self.previous.__class__.__name__}")

    def __repr__(self) -> str:
        return str(self)

    def new(self,
            target: Optional[str] = None,
            action: Optional[str] = None,
            payload: Optional[str] = None,
            source: Optional[str] = None
            ) -> Self:
        """
        Returns a new Message using any args given, defaulting to self attributes where none are provided.
        Self is assigned to 'previous' attribute.
        :param target: The module which the Message should be sent to.
        :param action: Which method withing the module the dispatcher should pass the message to.
        :param payload: The data for use by the target's action method.
        :param source: Where the Message has come from.
        :return: New Message instance based on self.
        """
        target = target or self.target
        action = action or self.action
        payload = payload or self.payload
        source = source or self.source

        return Message(target, action, payload, source, self)

    def get_first_message(self):
        if self.previous is None:
            return self
        return self.previous.get_first_message()
