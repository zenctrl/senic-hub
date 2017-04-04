import json
import logging
import time

from collections import defaultdict
from pprint import pformat
from threading import Thread

import websocket


logger = logging.getLogger(__name__)


class HomeAssistant(Thread):
    """
    Listens on events & state change notification through HASS WS interface.

    """
    def __init__(self, url, ws_connection=None, on_connect=None, on_disconnect=None):
        super().__init__(daemon=True)

        self.request_id = 1
        self.event_subscription_id = None

        self.connection_state_listeners = {
            "on_connect": on_connect,
            "on_disconnect": on_disconnect,
        }

        self.url = url
        self.connection = ws_connection

        self.stopping = False
        self.response_callbacks = {}  # req_id: callback

        self.state_listeners = defaultdict(list)  # entity_id: [callback1, ...]

    def connect(self, reconnect=False, reconnect_timeout=5):
        self.connection = None

        if reconnect:
            logger.warn("Home Assistant connection lost! Trying to reconnect...")

            on_disconnect_listener = self.connection_state_listeners["on_disconnect"]
            if on_disconnect_listener:
                on_disconnect_listener()

        while not self.connection:
            try:
                self.connection = create_connection("{}/api/websocket".format(self.url))
            except (ConnectionRefusedError, ConnectionResetError):
                logger.error("Failed to connect to Home Assistant! Retrying in %s seconds...", reconnect_timeout)
                time.sleep(reconnect_timeout)

        result = self.wait_for_message()
        if not result:
            return

        logger.info("Connected to Home Assistant %s", result["ha_version"])

        self.subscribe_to_events()

        on_connect_listener = self.connection_state_listeners["on_connect"]
        if on_connect_listener:
            on_connect_listener()

    def wait_for_message(self):
        try:
            message = json.loads(self.connection.recv())
        except (ConnectionResetError, WebSocketConnectionClosedException):
            self.connect(reconnect=True)
            return
        else:
            return message

    def prepare_request(self, request_type, **extra_args):
        data = {"id": self.request_id, "type": request_type}
        data.update(extra_args)
        self.request_id += 1
        return data

    def send_request(self, request, callback=None):
        if callback:
            self.response_callbacks[request["id"]] = callback

        logger.debug("Sending request:")
        logger.debug(pformat(request))

        try:
            self.connection.send(json.dumps(request))
        except BrokenPipeError:
            self.connect(reconnect=True)
            return

        if not callback:
            result = self.wait_for_message()
            if not result:
                return

            if not (result["id"] == request["id"] and
                    result["type"] == "result" and
                    result["success"] is True):

                logger.error(result)
                return None
            else:
                return result

    def subscribe_to_events(self):
        result = self.send_request(self.prepare_request("subscribe_events"))
        if result:
            self.event_subscription_id = result["id"]

            logger.debug("Subscibed to events:")
            logger.debug(pformat(result))
        else:
            logger.critical("Unable to subscribe to HA events...")
            raise ValueError("Error subscribing to HA Events")

    def run(self):
        if not self.connection:
            self.connect()

        while not self.stopping:
            result = self.wait_for_message()
            if not result:
                continue

            if result["type"] == "event":
                if (result["event"]["event_type"] == "state_changed" and
                   result["id"] == self.event_subscription_id):
                    self.process_event(result["event"])

            elif result["type"] == "result":
                if self.process_response_callbacks(result):
                    continue
                else:
                    logger.debug("Got result w/o callback: %s", result)
            else:
                logger.debug("Unknown HA message: %s", result)

    def process_event(self, payload):
        entity_id = payload["data"]["entity_id"]

        callbacks = self.state_listeners.get(entity_id, [])
        for callback in callbacks:
            callback(payload)

    def register_state_listener(self, entity_id, callback):
        self.state_listeners[entity_id].append(callback)

    def unregister_state_listener(self, entity_id):
        self.state_listeners.pop(entity_id, None)

    def process_response_callbacks(self, result):
        callback = self.response_callbacks.pop(result["id"])
        if callback:
            callback(result)
        return callback

    def call_service(self, domain, service, data, callback):
        request = self.prepare_request("call_service", domain=domain,
                                       service=service, service_data=data)

        self.send_request(request, callback)

    def get_state(self, entity_id, callbacks):
        request = self.prepare_request("get_states")

        def get_state_callback(response):
            state = self.find_entity_state(response["result"], entity_id)
            if state:
                for callback in callbacks:
                    callback(state)
            else:
                logger.error("Can't determine state of %s", entity_id)

        self.send_request(request, get_state_callback)

    def find_entity_state(self, states, entity_id):
        return next((x for x in states if x["entity_id"] == entity_id), None)

    def stop(self):
        self.stopping = True
