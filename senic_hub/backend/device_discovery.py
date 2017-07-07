import functools
import json
import logging
import xml.etree.ElementTree as ET

from copy import deepcopy
from enum import IntEnum
from requests.exceptions import ConnectionError

import requests

from .network_discovery import NetworkDiscovery


SUPPORTED_DEVICES = [
    "bose_soundtouch",
    "philips_hue",
    "sonos",
]


DISCOVERY_TIMESTAMP_FIELD = "discovered"


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


def discover_devices(devices, now):
    all_devices = []
    known_devices = deepcopy(devices)

    discovered_devices = discover()
    for device in discovered_devices:
        # make sure we get updates for devices we already had discovered before
        existing_device = next((d for d in known_devices if d["id"] == device["id"]), None)
        if existing_device:
            # device already known, check if we should update any fields
            if {k: v for k, v in existing_device.items() if k != DISCOVERY_TIMESTAMP_FIELD} == device:
                # all fields match, use the already known device
                continue
            else:
                # fields don't match, device will added as new
                known_devices.remove(existing_device)

        device[DISCOVERY_TIMESTAMP_FIELD] = str(now)
        all_devices.append(device)

    # add already known devices that were not found in this discovery
    # run or it was found that they didn't have any updates
    all_devices.extend(known_devices)

    return sorted(all_devices, key=lambda d: d["id"])


def discover(discovery_class=NetworkDiscovery):
    """
    Return a list of all discovered devices.

    :param discovery_class: Allow overriding what class to use for
    discovery. Used only in unit tests.

    """
    logger.info("Starting device discovery...")

    devices = []

    netdisco = discovery_class(SUPPORTED_DEVICES)
    netdisco.scan()

    for device_type in netdisco.discover():
        for device_info in netdisco.get_info(device_type):
            device_description = get_device_description(device_type, device_info)
            logger.info("Discovered %s device with ip %s", device_type, device_description["ip"])
            devices.append(device_description)

    netdisco.stop()
    logger.info("Device discovery finished.")

    return devices


def get_device_description(device_type, device_info):
    if device_type == "philips_hue":
        device_class = PhilipsHueBridgeDeviceDescription
    elif device_type == "bose_soundtouch":
        device_class = SoundtouchDeviceDescription
    else:
        device_class = SonosSpeakerDeviceDescription

    return device_class(device_info).device_description


class username_required:
    def __init__(self, method):
        self.method = method

    def __call__(self, instance, *args, **kwargs):
        if instance.username is None:
            raise UnauthenticatedDeviceError()

        return self.method(instance, *args, **kwargs)

    def __get__(self, instance, instancetype):
        return functools.partial(self.__call__, instance)


class PhilipsHueBridgeApiClient:
    def __init__(self, ip_address, username=None):
        self.ip_address = ip_address
        self.bridge_url = "http://{}/api".format(self.ip_address)
        self.app_name = "senic hub#192.168.1.12"  # TODO get real IP of the hub

        self.username = username

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
        except ConnectionError:
            pass

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


class SoundtouchDeviceDescription:
    def __init__(self, device_info):
        self.ip_address, self.port = device_info
        self.name = "Bose Soundtouch"

    @property
    def device_description(self):
        return {
            "id": self.ip_address.replace('.', '_'),
            "type": "soundtouch",
            "ip": self.ip_address,
            "port": self.port,
            "name": self.name,
            "authenticationRequired": False,
            "extra": {},
        }


class SonosSpeakerDeviceDescription:
    def __init__(self, device_info):
        self.ip_address = device_info
        response = requests.get('http://{}:1400/xml/device_description.xml'.format(self.ip_address))
        if response.status_code != 200:
            logger.warn("Response from Sonos speaker %s: status_code: %s, body: %s", self.ip_address,
                        response.status_code, response.text)
            raise UpstreamError(error_type=response.status_code)

        self.xml = ET.fromstring(response.text)

        device = self.xml.find('{urn:schemas-upnp-org:device-1-0}device')
        self.name = device.findtext('{urn:schemas-upnp-org:device-1-0}friendlyName')
        self.room_name = device.findtext('{urn:schemas-upnp-org:device-1-0}roomName')
        self.udn = device.findtext('{urn:schemas-upnp-org:device-1-0}UDN')

    @property
    def device_description(self):
        return {
            "id": self.udn.split('_')[1].lower(),
            "type": "sonos",
            "ip": self.ip_address,
            "name": self.name,
            "authenticationRequired": False,
            "extra": {
                "roomName": self.room_name,
            },
        }


class PhilipsHueBridgeDeviceDescription:
    def __init__(self, device_info):
        self.bridge_url = device_info[1]
        url = '{}description.xml'.format(self.bridge_url)
        response = requests.get(url)
        if response.status_code != 200:
            logger.warn("Response from Hue bridge %s: status_code: %s, body: %s", url, response.status_code, response.text)
            raise UpstreamError(error_type=response.status_code)

        xml = ET.fromstring(response.text)

        device = xml.find('{urn:schemas-upnp-org:device-1-0}device')
        self.serial_number = device.findtext('{urn:schemas-upnp-org:device-1-0}serialNumber')
        self.name = device.findtext('{urn:schemas-upnp-org:device-1-0}friendlyName')

    @property
    def device_description(self):
        return {
            "id": self.serial_number.lower(),
            "type": "philips_hue",
            "ip": self.bridge_url.split("http://")[1].split(":")[0],
            "name": self.name,
            "authenticationRequired": True,
            "extra": {},
        }
