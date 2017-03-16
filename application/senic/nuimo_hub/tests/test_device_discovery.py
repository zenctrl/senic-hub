from unittest.mock import MagicMock

from pytest import fixture

import responses

from senic.nuimo_hub.device_discovery import discover, extract_philips_hue_bridge_ip, make_device_description


@fixture
def philips_hue_device_info():
    return ("", "http://127.0.0.1:80")


@fixture
def sonos_device_info():
    return "192.168.1.42"


def test_extract_philips_hue_bridge_ip(philips_hue_device_info):
    assert extract_philips_hue_bridge_ip(philips_hue_device_info) == "127.0.0.1"


@responses.activate
def test_make_device_description_philips(philips_hue_device_info, philips_hue_bridge_description):
    responses.add(responses.GET, 'http://127.0.0.1/description.xml', body=philips_hue_bridge_description, status=200)
    expected = {
        "id": "ph1",
        "name": "Philips Hue bridge",
        "authenticationRequired": True,
        "authenticated": False,
        "type": "philips_hue",
        "ip": "127.0.0.1",
        "ha_entity_id": "light.all_lights",
    }
    assert make_device_description("philips_hue", philips_hue_device_info) == expected


@responses.activate
def test_make_device_description_sonos(sonos_device_info, sonos_speaker_description):
    responses.add(responses.GET, 'http://192.168.1.42:1400/xml/device_description.xml', body=sonos_speaker_description, status=200)
    expected = {
        "id": "123",
        "type": "sonos",
        "ip": "192.168.1.42",
        "authenticationRequired": False,
        "authenticated": False,
        "name": "192.168.1.42 Foo Bar",
        "ha_entity_id": "media_player.foo_bar",
    }
    assert make_device_description("sonos", sonos_device_info) == expected


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


@responses.activate
def test_discover_philips_hue_device(philips_hue_bridge_description):
    responses.add(responses.GET, 'http://127.0.0.1/description.xml', body=philips_hue_bridge_description, status=200)
    expected = {
        "id": "ph1",
        "name": "Philips Hue bridge",
        "authenticationRequired": True,
        "authenticated": False,
        "type": "philips_hue",
        "ip": "127.0.0.1",
        "ha_entity_id": "light.all_lights",
    }
    assert discover(MockPhilipsDiscovery) == [expected]
