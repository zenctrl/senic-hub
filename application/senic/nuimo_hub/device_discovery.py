import functools
import json
import logging
import re

import xml.etree.ElementTree as ET
from enum import IntEnum

from netdisco.discovery import NetworkDiscovery

import requests


SUPPORTED_DEVICES = [
    "philips_hue",
    "sonos",
]


class UnauthenticatedDeviceError(Exception):
    message = "Device not authenticated..."


class UpstreamError(Exception):
    def __init__(self, error_type=None):
        self.error_type = error_type
        self.message = "Received error from the upstream device! Type: {}".format(self.error_type)


class PhilipsHueBridgeError(IntEnum):
    unauthorized = 1
    button_not_pressed = 101


logger = logging.getLogger(__name__)


def discover(discovery_class=NetworkDiscovery):
    logger.info("Starting device discovery...")

    devices = []

    netdisco = discovery_class()
    netdisco.scan()

    for device_type in netdisco.discover():
        if device_type not in SUPPORTED_DEVICES:
            continue

        for device_info in netdisco.get_info(device_type):
            device_description = make_device_description(device_type, device_info)
            if device_description:
                devices.append(device_description)

    netdisco.stop()
    logger.info("Device discovery finished.")

    return devices


def make_device_description(device_type, device_info):
    if device_type == "philips_hue":
        bridge_ip = extract_philips_hue_bridge_ip(device_info)
        device = PhilipsHueBridge(bridge_ip)
    elif device_type == "sonos":
        device = SonosSpeaker(device_info)

    logger.info("Discovered %s device with ip %s", device_type, device.device_description["ip"])

    return device.device_description


def extract_philips_hue_bridge_ip(device_info):
    _, bridge_url = device_info

    result = re.search("http://([\.0-9]+):80", bridge_url)
    if result:
        return result.group(1)


class username_required:
    def __init__(self, method):
        self.method = method

    def __call__(self, instance, *args, **kwargs):
        if instance.username is None:
            raise UnauthenticatedDeviceError()

        return self.method(instance, *args, **kwargs)

    def __get__(self, instance, instancetype):
        return functools.partial(self.__call__, instance)


class PhilipsHueBridge:
    def __init__(self, ip_address, username=None):
        self.ip_address = ip_address
        self.bridge_url = "http://{}/api".format(self.ip_address)
        self.app_name = "senic hub#192.168.1.12"  # TODO get real IP of the hub

        self.username = username

        self._http_session = requests.Session()

        self.config = self.get_config()

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
            error_type = data["error"]["type"]
            if error_type in [
                    PhilipsHueBridgeError.unauthorized,
                    PhilipsHueBridgeError.button_not_pressed,
            ]:
                raise UnauthenticatedDeviceError()
            else:
                raise UpstreamError(error_type=error_type)

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
            if response:
                self.username = response["success"]["username"]
        except UnauthenticatedDeviceError:
            self.username = None

        return self.username

    def is_authenticated(self):
        # Verify that we can still authenticate with the bridge using
        # the username that we have saved. We do this by getting the
        # bridge configuration.
        try:
            self.get_state()
        except UnauthenticatedDeviceError:
            return False

        return True

    @username_required
    def get_state(self):
        url = "{}/{}".format(self.bridge_url, self.username)
        return self._request(url)

    @username_required
    def get_lights(self):
        url = "{}/{}/lights".format(self.bridge_url, self.username)
        return self._request(url)

    def get_config(self):
        url = 'http://{}/description.xml'.format(self.ip_address)
        response = requests.get(url)
        if response.status_code != 200:
            logger.debug("Response from Hue bridge %s: status_code: %s, body: %s", url, response.status_code, response.text)
            raise UpstreamError(error_type=response.status_code)

        xml = ET.fromstring(response.text)

        device = xml.find('{urn:schemas-upnp-org:device-1-0}device')
        serial_number = device.findtext('{urn:schemas-upnp-org:device-1-0}serialNumber')
        name = device.findtext('{urn:schemas-upnp-org:device-1-0}friendlyName')

        return {
            "bridgeid": serial_number,
            "name": name,
        }

    @property
    def device_description(self):
        return {
            "id": self.config["bridgeid"].lower(),
            "type": "philips_hue",
            "ip": self.ip_address,
            "name": self.config["name"],
            "authenticationRequired": True,
            "authenticated": self.is_authenticated(),
            "ha_entity_id": "light.all_lights",
        }


class SonosSpeaker:
    def __init__(self, speaker_ip):
        self.ip_address = speaker_ip
        response = requests.get('http://{}:1400/xml/device_description.xml'.format(self.ip_address))
        self.xml = ET.fromstring(response.text)

    @property
    def device_description(self):
        device = self.xml.find('{urn:schemas-upnp-org:device-1-0}device')
        name = device.findtext('{urn:schemas-upnp-org:device-1-0}friendlyName')
        room_name = device.findtext('{urn:schemas-upnp-org:device-1-0}roomName').replace(" ", "_").lower()
        udn = device.findtext('{urn:schemas-upnp-org:device-1-0}UDN').split('_')[1].lower()

        return {
            "id": udn,
            "type": "sonos",
            "ip": self.ip_address,
            "name": name,
            "authenticationRequired": False,
            "authenticated": False,
            "ha_entity_id": "media_player.{}".format(room_name),
        }
