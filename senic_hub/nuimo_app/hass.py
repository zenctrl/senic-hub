import json
import logging

from collections import defaultdict
from pprint import pformat
from threading import Thread
from time import sleep, time

import websocket


logger = logging.getLogger(__name__)


class HomeAssistantConnection(Thread):
    def __init__(self, url, on_open, on_message, on_close):
        super().__init__()

        self.websocket_url = "ws://{}/api/websocket".format(url)

        self.on_open_callback = on_open
        self.on_message_callback = on_message
        self.on_close_callback = on_close

        self.websocket = None

    @property
    def connected(self):
        return self.websocket and self.websocket.sock.connected

    def on_open(self, ws):
        logger.info("Connected to Home Assistant url: %s", self.websocket_url)

        self.on_open_callback()

    def on_message(self, ws, message):
        self.on_message_callback(json.loads(message))

    def on_error(self, ws, error):
        logger.error("Connection failed with: %s", error)
        self.websocket = None

    def on_close(self, ws):
        self.websocket = None
        self.on_close_callback()

    def send(self, message):
        self.websocket.send(json.dumps(message))

    def run(self):
        logger.info("Connecting to Home Assistant url: %s...", self.websocket_url)

        self.websocket = websocket.WebSocketApp(
            self.websocket_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.websocket.run_forever()

    def stop(self):
        if self.websocket:
            self.websocket.close()
            self.websocket = None


class HomeAssistant(Thread):
    """
    Listens on events & state change notification through Home
    Assistant websocket interface and sends commands to services
    registered with Home Assistant.

    """
    def __init__(self, url, on_connect=None, on_disconnect=None):
        super().__init__()

        self.request_id = 1
        self.event_subscription_id = None

        self.connection_state_listeners = {
            "on_connect": on_connect,
            "on_disconnect": on_disconnect,
        }

        self.url = url
        self.connection = None

        self.reconnection_interval = 5  # seconds

        self.stopping = False

        self.result_callbacks = None
        self.state_listeners = defaultdict(list)  # entity_id: [callback1, ...]

    def connect(self):
        self.result_callbacks = {}  # req_id: callback
        self.connection = HomeAssistantConnection(
            self.url,
            on_open=self.on_connect,
            on_message=self.on_message,
            on_close=self.on_disconnect,
        )
        self.connection.start()

        self.next_reconnect_time = time() + self.reconnection_interval

    def on_connect(self):
        on_connect_listener = self.connection_state_listeners["on_connect"]
        if on_connect_listener:
            on_connect_listener()

        self.subscribe_to_events()

    def on_message(self, message):
        if message["type"] == "event":
            if (message["event"]["event_type"] == "state_changed" and message["id"] == self.event_subscription_id):
                self.process_event(message["event"])

        elif message["type"] == "result":
            if self.process_result(message):
                return
            else:
                logger.debug("Got result w/o callback: %s", message)

        elif message["type"] == "auth_ok":
            pass

        else:
            logger.debug("Unknown HA message: %s", message)

    def on_disconnect(self):
        if self.connection:
            self.connection.stop()
            self.connection = None

        on_disconnect_listener = self.connection_state_listeners["on_disconnect"]
        if on_disconnect_listener:
            on_disconnect_listener()

        if self.stopping:
            return

        logger.warn("Home Assistant connection lost! Trying to reconnect in %s seconds...", self.reconnection_interval)
        self.next_reconnect_time = time() + self.reconnection_interval

    def prepare_request(self, request_type, **extra_args):
        data = {"id": self.request_id, "type": request_type}
        data.update(extra_args)
        self.request_id += 1
        return data

    def send_request(self, request, success_callback, error_callback):
        self.result_callbacks[request["id"]] = success_callback

        logger.debug("Sending request id: %s", request['id'])
        logger.debug(pformat(request))

        try:
            if self.connection and self.connection.connected:
                self.connection.send(request)
            else:
                error_callback()

        except BrokenPipeError:
            error_callback()

    def subscribe_to_events(self):
        def callback(result=None):
            if result is not None:
                self.event_subscription_id = result["id"]
            else:
                logger.critical("Unable to subscribe to Home Assistant events...")

        self.send_request(self.prepare_request("subscribe_events"), callback, callback)

    def run(self):
        self.connect()

        while not self.stopping:
            if not (self.connection and self.connection.connected):
                if time() >= self.next_reconnect_time:
                    self.connect()

            # TODO dispatch events to Home Assistant from here...

            sleep(0.01)

    def process_event(self, payload):
        entity_id = payload["data"]["entity_id"]

        callbacks = self.state_listeners.get(entity_id, [])
        for callback in callbacks:
            callback(payload)

    def register_state_listener(self, entity_id, callback):
        self.state_listeners[entity_id].append(callback)

    def unregister_state_listener(self, entity_id):
        self.state_listeners.pop(entity_id, None)

    def process_result(self, result):
        logger.debug("Received result id: %s success: %s result:", result["id"], result["success"])
        logger.debug(pformat(result["result"]))

        callback = self.result_callbacks.pop(result["id"])
        if callback:
            callback(result)

        return callback

    def call_service(self, domain, service, data, success_callback, error_callback):
        request = self.prepare_request("call_service", domain=domain, service=service, service_data=data)

        self.send_request(request, success_callback, error_callback)

    def get_state(self, entity_id, callback, error_callback):
        request = self.prepare_request("get_states")

        def get_state_callback(response):
            state = self.find_entity_state(response["result"], entity_id)
            if state:
                callback(state)
            else:
                logger.error("Can't determine state of %s", entity_id)

        self.send_request(request, get_state_callback, error_callback)

    def find_entity_state(self, states, entity_id):
        return next((x for x in states if x["entity_id"] == entity_id), None)

    def stop(self):
        self.stopping = True

        if self.connection:
            self.connection.stop()
