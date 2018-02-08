import functools
import json
import logging
import logging.config
import os
import signal
import sys
import time
import xml.etree.ElementTree as ET

from copy import deepcopy
from enum import IntEnum

import click
import requests

from os.path import abspath
from datetime import datetime, timedelta
from pyramid.paster import get_app
from requests.exceptions import ConnectionError
from json.decoder import JSONDecodeError

from .lockfile import open_locked
from .network_discovery import NetworkDiscovery


if os.path.isfile('/etc/senic_hub.ini'):  # pragma: no cover
    logging.config.fileConfig(
        '/etc/senic_hub.ini', disable_existing_loggers=False
    )


logger = logging.getLogger(__name__)


SUPPORTED_DEVICES = [
    "philips_hue",
    "sonos",
]


DEFAULT_SCAN_INTERVAL_SECONDS = 1 * 60  # 1 minute


class UnsupportedDeviceTypeException(Exception):
    pass


@click.command(help='scan for devices in local network and store their description in a file')
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help='app configuration file')
@click.option('--verbose', '-v', count=True, help="Print info messages (-vv for debug messages)")
def command(config, verbose):  # pragma: no cover
    app = get_app(abspath(config), name='senic_hub')

    if verbose >= 2:
        logger.setLevel(logging.DEBUG)
    elif verbose >= 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)

    devices_path = app.registry.settings['devices_path']
    scan_interval_seconds = int(app.registry.settings.get(
        'device_scan_interval_seconds', DEFAULT_SCAN_INTERVAL_SECONDS))

    # install Ctrl+C handler
    def sigint_handler(*args):
        logger.info('Stopping...')
        sys.exit(0)
    signal.signal(signal.SIGINT, sigint_handler)

    while True:
        now = datetime.utcnow()
        discover_and_merge_devices(devices_path, now)

        next_scan = now + timedelta(seconds=scan_interval_seconds)
        logger.info("Next device discovery run scheduled for %s", next_scan)
        time.sleep(scan_interval_seconds)


def discover_and_merge_devices(devices_path, now):
    discovered_devices = discover_devices()

    try:
        with open_locked(devices_path, 'r') as f:
            known_devices = json.load(f)
    except (FileNotFoundError, JSONDecodeError) as e:
        logger.error(e)
        known_devices = []

    merged_devices = merge_devices(known_devices, discovered_devices, now)

    add_authentication_status(merged_devices)

    try:
        with open_locked(devices_path, 'w') as f:
            json.dump(merged_devices, f)
    except (FileNotFoundError, JSONDecodeError) as e:  # pragma: no cover
        logger.error(e)


def discover_devices(discovery_class=NetworkDiscovery):
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


def merge_devices(known_devices, discovered_devices, now):
    # TODO: Do we need to make a deep copy? Are arrays not passed by-value, but by-ref?
    known_devices = deepcopy(known_devices)

    # TODO: `merged_devices` can be directly assigned with a list comprehension
    merged_devices = []

    for device in discovered_devices:
        # make sure we get updates for devices we already had discovered before
        known_device = next((d for d in known_devices if d["id"] == device["id"]), None)
        if known_device:
            known_devices.remove(known_device)

            # Copy "extra" attributes from existing device if not present in newly found
            # device. These attributes are typically added later such as during
            # authentication of Philipe Hue bridge.
            merged_extra = known_device.get('extra', None)
            if merged_extra:
                merged_extra.update(device.get('extra', {}))
                device['extra'] = merged_extra

        device['discovered'] = str(now)
        merged_devices.append(device)

    # add already known devices that were not found in this discovery
    # run or it was found that they didn't have any updates
    merged_devices.extend(known_devices)

    return sorted(merged_devices, key=lambda d: d["id"])


def add_authentication_status(devices):
    for device in devices:
        if not device["authenticationRequired"]:
            device["authenticated"] = True
            continue

        if device["type"] == "philips_hue":
            api = PhilipsHueBridgeApiClient(device["ip"], device['extra'].get('username'))
            device["authenticated"] = api.is_authenticated()
        else:
            device["authenticated"] = True


class UnauthenticatedDeviceError(Exception):
    message = "Device not authenticated..."


class UpstreamError(Exception):
    def __init__(self, error_type=None):
        self.error_type = error_type
        self.message = "Received error from the upstream device! Type: {}".format(self.error_type)


class PhilipsHueBridgeError(IntEnum):
    unauthorized = 1
    button_not_pressed = 101


def get_device_description(device_type, device_info):
    if device_type == "philips_hue":
        device_class = PhilipsHueBridgeDeviceDescription
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

        logger.info(
            "Trying to authenticate with Hue bridge: %s" % self.bridge_url
        )
        return self.username

    def is_authenticated(self):
        # Verify that we can still authenticate with the bridge using
        # the username that we have saved. We do this by getting the
        # bridge configuration.
        try:
            self.get_state()
        except UnauthenticatedDeviceError:
            return False

        logger.info(
            "Authenticated with Hue bridge %s: " % self.bridge_url
        )
        return True

    @username_required
    def get_state(self):
        url = "{}/{}".format(self.bridge_url, self.username)
        return self._request(url)

    @username_required
    def get_lights(self):
        url = "{}/{}/lights".format(self.bridge_url, self.username)
        return self._request(url)


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
