from multiprocessing.queues import Queue

from utils import Utils
from repo import Repo


class TCG:
    def __init__(self, p_q: Queue, db: Repo):
        self.p_q = p_q
        self.db = db
        self.dispatch_map = {
            "handle_custom": {
                "target": self.handle_custom
            },
            "handle_refresh_tcg": {
                "target": self.handle_refresh_tcg
            }
        }
        self.custom_command_map = {
            "offer": {
                "target": self.handle_trade_offer
            },
            "confirm": {
                "target": self.handle_trade_confirmed
            }
        }
        self.trade_history = {}
        self.card_owners = {}
        self.trade_map = {}
        self.trade_offers = {}
        self.registered_cards = {}
        self.last_trade_id = 0

    def _create_trade_offer(self, player_one: str, card_one: str, player_two: str):
        self.last_trade_id += 1

        trade_id = str(self.last_trade_id)

        self.trade_offers[trade_id] = {
            "player_one": player_one,
            "card_one": card_one,
            "player_one_confirmation": False,
            "card_one_received": False,
            "player_two": player_two,
            "card_two": None,
            "player_two_confirmation": False,
            "card_two_received": False,
        }

    def _match_trade(self, trade_id: str, card_two: str):
        self.trade_map[trade_id] = self.trade_offers.pop(trade_id)
        self.trade_map[trade_id]["card_two"] = card_two

    def _finalise_trade(self, trade_id: str):
        trade = self.trade_map[trade_id]
        actions = []

        send_data = {
            "player": trade["player_one"],
            "plugin": "lb_tcg",
            "command": "complete",
            "payload": f"{trade_id}",
        }

        actions.append(Utils.gen_send_action("custom", send_data))

        send_data = {
            "player": trade["player_two"],
            "plugin": "lb_tcg",
            "command": "complete",
            "payload": f"{trade_id}",
        }

        actions.append(Utils.gen_send_action("custom", send_data))

        actions.append({
            "target": "game",
            "action": "send_ws_message",
            "payload": f"GIVE_TCG_CARD={trade['player_two']}~{trade['card_one']}",
            "source": "tcg",
        })

        actions.append({
            "target": "game",
            "action": "send_ws_message",
            "payload": f"GIVE_TCG_CARD={trade['player_one']}~{trade['card_two']}",
            "source": "tcg",
        })

        for action in actions:
            self.p_q.put(action)

        self.card_owners.pop(trade["card_one"])
        self.card_owners.pop(trade["card_two"])
        self.registered_cards.pop(trade["card_one"])
        self.registered_cards.pop(trade["card_two"])

        self.trade_history[trade_id] = self.trade_map.pop(trade_id)

        print(self.registered_cards)
        print(self.trade_map)
        print(self.card_owners)
        print(self.trade_offers)
        print(self.trade_history)

    def _broadcast_trade(self, trade_id: str):
        trade = self.trade_map[trade_id]
        actions = []

        send_data = {
            "player": trade["player_one"],
            "plugin": "lb_tcg",
            "command": "trade",
            "payload": f"{trade['card_one']};{trade['card_two']};{trade_id}",
        }

        actions.append(Utils.gen_send_action("custom", send_data))

        send_data = {
            "player": trade["player_two"],
            "plugin": "lb_tcg",
            "command": "trade",
            "payload": f"{trade['card_two']};{trade['card_one']};{trade_id}",
        }

        actions.append(Utils.gen_send_action("custom", send_data))

        for action in actions:
            self.p_q.put(action)

    def dispatch(self, action: dict):
        target_dict = self.dispatch_map.get(action["action"], None)

        if target_dict is None:
            print(f"TCG dispatch error: No handler for {action['action']}")
            return

        target_dict["target"](action)

    def handle_custom(self, action: dict):
        parsed_custom = action["payload"]
        target_dict = self.custom_command_map.get(parsed_custom["command"], None)

        if target_dict is None:
            print(f"TCG custom dispatch error: No handler for {parsed_custom['command']}")
            return

        new_payload = {
            "player": parsed_custom["player"],
            "parsed_command": {
                'callback_id': parsed_custom["callback_id"],
                'plugin': parsed_custom["plugin"],
                'command': parsed_custom["command"],
                'payload': parsed_custom["payload"],
                'anwin_formatted': parsed_custom["anwin_formatted"],
                'player_offline': parsed_custom["player_offline"],
                "time": parsed_custom["time"],
            },
        }

        new_action = {
            "target": "tcg",
            "action": parsed_custom["command"],
            "payload": new_payload,
            "source": "custom",
        }

        target_dict["target"](new_action)

    def handle_trade_offer(self, action: dict):
        sender = action["payload"]["player"]["username"]
        payload = action["payload"]["parsed_command"]["payload"]

        split_payload = payload.split(";", 1)

        if len(split_payload) != 2:
            print(f"Invalid payload: {payload}")
            return

        receiver = split_payload[0]
        card_id = split_payload[1]

        self.card_owners[card_id] = sender

        match_found = False

        for trade_id, offer in self.trade_offers.items():
            if offer["player_one"] == receiver and offer["player_two"] == sender:
                self._match_trade(trade_id, card_id)
                self._broadcast_trade(trade_id)
                match_found = True
                break

        if not match_found:
            self._create_trade_offer(sender, card_id, receiver)

    def handle_trade_confirmed(self, action: dict):
        sender = action["payload"]["player"]["username"]
        trade_id = action["payload"]["parsed_command"]["payload"]

        trade = self.trade_map.get(trade_id, None)

        if not trade:
            print(f"Invalid trade id {trade_id}")

        if trade["player_one"] == sender:
            trade["player_one_confirmation"] = True
        elif trade["player_two"] == sender:
            trade["player_two_confirmation"] = True
        else:
            print(f"Invalid player {sender} attempted to confirm trade {trade_id}.")

    def handle_refresh_tcg(self, action: dict):
        payload = action["payload"]
        received_time = payload["time"]
        card_list = []

        raw_card_data = payload["payload"].split("~")

        if len(raw_card_data) < 3:
            return

        for i in range(0, len(raw_card_data), 3):
            card_list.append(raw_card_data[i])

        for card_id in card_list:
            if card_id in self.registered_cards:
                continue

            trade_id = None

            if card_id in self.card_owners:
                source = self.card_owners[card_id]
            else:
                source = "unknown_source"

            for current_id, trade in self.trade_map.items():
                if card_id == trade["card_one"]:
                    trade["card_one_received"] = True
                    trade_id = current_id
                    break
                elif card_id == trade["card_two"]:
                    trade["card_two_received"] = True
                    trade_id = current_id
                    break
                else:
                    continue

            self.registered_cards[card_id] = {
                "source": source,
                "time_received": received_time,
                "trade_id": trade_id
            }

            if trade_id:
                trade = self.trade_map[trade_id]
                if trade["card_one_received"] and trade["card_two_received"]:
                    self._finalise_trade(trade_id)
