from unittest.mock import MagicMock

from pytest import fixture

from senic.nuimo_hub.device_discovery import discover, extract_philips_hue_bridge_ip, make_device_description


@fixture
def philips_hue_device_info():
    return ("", "http://127.0.0.1:80")


@fixture
def sonos_device_info():
    return "192.168.1.42"


@fixture
def unknown_device_info():
    return


def test_extract_philips_hue_bridge_ip(philips_hue_device_info):
    assert extract_philips_hue_bridge_ip(philips_hue_device_info) == "127.0.0.1"


def test_make_device_description_philips(philips_hue_device_info):
    expected = {
        "id": 0,
        "type": "philips_hue",
        "ip": "127.0.0.1",
    }
    assert make_device_description(0, "philips_hue", philips_hue_device_info) == expected


def test_make_device_description_sonos(sonos_device_info):
    expected = {
        "id": 1,
        "type": "sonos",
        "ip": "192.168.1.42",
    }
    assert make_device_description(1, "sonos", sonos_device_info) == expected


def test_make_device_description_unknown(unknown_device_info):
    assert make_device_description(1, "unknown", unknown_device_info) is None


class MockUnknownDeviceDiscovery(MagicMock):
    def discover(self):
        return ["unknown"]


def test_discover_unknow_devices():
    assert discover(MockUnknownDeviceDiscovery) == []


class MockPhilipsDiscovery(MagicMock):
    def discover(self):
        return ["philips_hue"]

    def get_info(self, device_type):
        return [("", "http://127.0.0.1:80")]


def test_discover_philips_hue_device():
    assert discover(MockPhilipsDiscovery) == [{
        "id": 0,
        "type": "philips_hue",
        "ip": "127.0.0.1",
    }]
