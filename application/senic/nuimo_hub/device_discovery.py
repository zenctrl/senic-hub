import logging
import re

from netdisco.discovery import NetworkDiscovery


SUPPORTED_DEVICES = [
    "philips_hue",
    "sonos",
]


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
