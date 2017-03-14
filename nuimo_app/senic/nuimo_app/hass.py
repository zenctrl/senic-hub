import json
import logging

from collections import defaultdict
from pprint import pformat
from threading import Thread

from websocket import create_connection


logger = logging.getLogger(__name__)


class HAListener(Thread):
    """
    Listens on events & state change notification through HASS WS interface.

    """
    def __init__(self, url, ws_connection=None):
        super().__init__(daemon=True)

        self.request_id = 1
        self.event_subscription_id = None

        self.connection = ws_connection
        if not self.connection:
            self.connect(url)

        self.stopping = False
        self.response_callbacks = {}  # req_id: callback

        self.state_listeners = defaultdict(list)  # {entity_id1, ...}: [callback, ...]

    def connect(self, url):
        self.connection = create_connection("{}/api/websocket".format(url))
        result = json.loads(self.connection.recv())
        logger.info("Connected to Home Assistant %s", result["ha_version"])

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
        self.connection.send(json.dumps(request))

        if not callback:
            result = json.loads(self.connection.recv())

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
        self.subscribe_to_events()

        while not self.stopping:
            logger.debug("waiting for HA events...")
            result = json.loads(self.connection.recv())

            if result["type"] == "event":
                if (result["event"]["event_type"] == "state_changed" and
                   result["id"] == self.event_subscription_id):
                    self.process_event(result["event"])

            elif result["type"] == "result":
                if self.process_callbacks(result):
                    continue
                else:
                    logger.debug("Got result w/o callback: %s", result)
            else:
                logger.debug("Unknown HA message: %s", result)

    def process_event(self, payload):
        entity_id = payload["data"]["entity_id"]

        listeners_to_notify = [x for x in self.state_listeners if entity_id in x]

        for listener in listeners_to_notify:
            callbacks = self.state_listeners[listener]
            for callback in callbacks:
                callback(payload)

    def register_state_listener(self, entity_ids, callback):
        self.state_listeners[entity_ids].append(callback)

    def unregister_state_listener(self, entity_ids):
        self.state_listeners.pop(entity_ids, None)

    def process_callbacks(self, result):
        callback = self.response_callbacks.pop(result["id"])
        if callback:
            callback(result)
        return callback

    def call_service(self, domain, service, data, callback):
        request = self.prepare_request("call_service", domain=domain,
                                       service=service, service_data=data)

        self.send_request(request, callback)

    def get_state(self, entity_ids, callback):
        request = self.prepare_request("get_states")

        def get_state_callback(response):
            entity_states = []
            for entity_id in entity_ids:
                state = self.find_entity_state(response["result"], entity_id)
                if not state:
                    logger.error("Can't determine state of %s", entity_id)
                else:
                    entity_states.append(state)

            callback(entity_states)

        self.send_request(request, get_state_callback)

    def find_entity_state(self, states, entity_id):
        return next((x for x in states if x["entity_id"] == entity_id), None)

    def stop(self):
        self.stopping = True
