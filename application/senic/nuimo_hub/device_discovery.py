import json
import logging
import os.path
import re

from enum import IntEnum

from netdisco.discovery import NetworkDiscovery

import requests


SUPPORTED_DEVICES = [
    "philips_hue",
    "sonos",
]


class UnauthenticatedDeviceError(Exception):
    message = "Device not authenticated..."


class PhilipsHueBridgeError(IntEnum):
    unauthorized = 1


logger = logging.getLogger(__name__)


def discover(discovery_class=NetworkDiscovery):
    logger.info("Starting device discovery...")

    devices = []

    netdisco = discovery_class()
    netdisco.scan()

    device_id = 0
    for device_type in netdisco.discover():
        if device_type not in SUPPORTED_DEVICES:
            continue

        for device_info in netdisco.get_info(device_type):
            description = make_device_description(device_id, device_type, device_info)
            if description:
                devices.append(description)
                device_id += 1

    netdisco.stop()
    logger.info("Device discovery finished.")

    return devices


def make_device_description(device_id, device_type, device_info):
    if device_type == "philips_hue":
        device_ip = extract_philips_hue_bridge_ip(device_info)
    elif device_type == "sonos":
        device_ip = device_info
    else:
        device_ip = None

    if device_ip:
        logger.info("Discovered %s device with ip %s", device_type, device_ip)

        return {
            "id": device_id,
            "type": device_type,
            "ip": device_ip,
        }
    else:
        logger.warn("Failed to extract IP address for %s from device info %s", device_type, device_info)


def extract_philips_hue_bridge_ip(device_info):
    _, bridge_url = device_info

    result = re.search("http://([\.0-9]+):80", bridge_url)
    if result:
        return result.group(1)


class PhilipsHueBridge:
    def __init__(self, ip_address, data_location):
        self.bridge_url = "http://{}/api".format(ip_address)
        self.state_file_path = os.path.join(data_location, ip_address)
        self.app_name = "senic hub#192.168.1.12"  # TODO get real IP of the hub

        self._username = None
        self._http_session = requests.Session()

    def _request(self, url, method="GET", payload=None, timeout=5):
        request = requests.Request(method, url, data=payload)
        response = self._http_session.send(request.prepare(), timeout=timeout)
        if response.status_code != 200:
            logger.debug("Response from Hue bridge %s: %s", url, response.status_code)
            return

        data = response.json()
        if isinstance(data, list):
            data = data[0]

        if "error" in data:
            logger.error("Response from Hue bridge %s: %s", self.bridge_url, data)
            if data["error"].get("type") == PhilipsHueBridgeError.unauthorized:
                raise UnauthenticatedDeviceError()

            return

        return data

    def authenticate(self):
        """
        Make the authentication requests to Philips Hue bridge.

        Caller has to make 2 requests. First request initiates the
        authentication handshake. Then user has to authenticate with
        the Philips Hue bridge by pressing the button on the bridge
        within 30 seconds. The second request will write the state
        file with the username in case of successful authentication.

        """
        try:
            payload = json.dumps({"devicetype": self.app_name})
            response = self._request(self.bridge_url, method="POST", payload=payload)
            if not response:
                return

            self._username = response["success"]["username"]

            with open(self.state_file_path, "w") as f:
                json.dump({"devicetype": self.app_name, "username": self._username}, f)

        except UnauthenticatedDeviceError:
            pass  # consume the exception

    def is_authenticated(self):
        # Verify that we can still authenticate with the bridge using
        # the username that we have saved. We do this by getting the
        # bridge configuration.
        try:
            self.get_state()
        except UnauthenticatedDeviceError:
            return False

        return True

    @property
    def username(self):
        if self._username:
            return self._username

        if os.path.exists(self.state_file_path):
            with open(self.state_file_path, "r") as f:
                data = json.load(f)

            self._username = data.get("username")

            return self._username

    def get_state(self):
        if self.username is None:
            raise UnauthenticatedDeviceError()

        url = "{}/{}".format(self.bridge_url, self.username)
        return self._request(url)

    def get_lights(self):
        if self.username is None:
            raise UnauthenticatedDeviceError()

        url = "{}/{}/lights".format(self.bridge_url, self.username)
        return self._request(url)
