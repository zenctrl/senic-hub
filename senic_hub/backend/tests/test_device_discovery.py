from datetime import datetime, timedelta
from unittest.mock import MagicMock

from pytest import fixture, raises

import responses

from senic_hub.backend.device_discovery import (
    DISCOVERY_TIMESTAMP_FIELD, UpstreamError, discover_devices, merge_devices, get_device_description)


@fixture
def philips_hue_bridge_device_info():
    return ("", "http://127.0.0.1:80/")


@fixture
def sonos_device_info():
    return "192.168.1.42"


@fixture
def soundtouch_device_info():
    return ("192.168.1.23", 8090)


@responses.activate
def test_get_device_description_of_philips_hue_bridge(philips_hue_bridge_device_info, philips_hue_bridge_description):
    responses.add(responses.GET, 'http://127.0.0.1:80/description.xml', body=philips_hue_bridge_description, status=200)
    expected = {
        "id": "ph1",
        "name": "Philips Hue bridge",
        "authenticationRequired": True,
        "type": "philips_hue",
        "ip": "127.0.0.1",
        "extra": {},
    }
    assert get_device_description("philips_hue", philips_hue_bridge_device_info) == expected


@responses.activate
def test_get_device_description_of_philips_hue_bridge_throws_when_getting_description_fails(philips_hue_bridge_device_info):
    responses.add(responses.GET, 'http://127.0.0.1:80/description.xml', status=404)
    with raises(UpstreamError) as e:
        get_device_description("philips_hue", philips_hue_bridge_device_info)
    assert e.value.error_type == 404


@responses.activate
def test_get_device_description_of_sonos_speaker(sonos_device_info, sonos_speaker_description):
    responses.add(responses.GET, 'http://192.168.1.42:1400/xml/device_description.xml', body=sonos_speaker_description, status=200)
    expected = {
        "id": "123",
        "type": "sonos",
        "ip": "192.168.1.42",
        "authenticationRequired": False,
        "name": "192.168.1.42 Foo Bar",
        "extra": {
            "roomName": "Foo Bar",
        },
    }
    assert get_device_description("sonos", sonos_device_info) == expected


@responses.activate
def test_get_device_description_of_soundtouch_speaker(soundtouch_device_info):
    expected = {
        "id": "192_168_1_23",
        "type": "soundtouch",
        "ip": "192.168.1.23",
        "port": 8090,
        "authenticationRequired": False,
        "name": "Bose Soundtouch",
        "extra": {},
    }
    assert get_device_description("bose_soundtouch", soundtouch_device_info) == expected


@responses.activate
def test_get_device_description_of_sonos_speaker_throws_when_getting_description_fails(sonos_device_info):
    responses.add(responses.GET, 'http://192.168.1.42:1400/xml/device_description.xml', status=404)
    with raises(UpstreamError) as e:
        get_device_description("sonos", sonos_device_info)
    assert e.value.error_type == 404


class MockPhilipsDiscovery(MagicMock):
    def scan(self):
        pass

    def stop(self):
        pass

    def discover(self):
        return ["philips_hue"]

    def get_info(self, device_type):
        return [("", "http://127.0.0.1:80/")]


@responses.activate
def test_discover_philips_hue_device(philips_hue_bridge_description):
    responses.add(responses.GET, 'http://127.0.0.1:80/description.xml', body=philips_hue_bridge_description, status=200)
    expected = {
        "id": "ph1",
        "name": "Philips Hue bridge",
        "authenticationRequired": True,
        "type": "philips_hue",
        "ip": "127.0.0.1",
        "extra": {},
    }
    assert discover_devices(MockPhilipsDiscovery) == [expected]


def test_discover_devices_for_the_first_time_return_all_devices():
    known_devices = []
    discovered_devices = [{
        "id": "1",
        "name": "first",
    }, {
        "id": "2",
        "name": "second",
    }]
    now = datetime.utcnow()
    expected = [{
        "id": "1",
        "name": "first",
        DISCOVERY_TIMESTAMP_FIELD: str(now),
    }, {
        "id": "2",
        "name": "second",
        DISCOVERY_TIMESTAMP_FIELD: str(now),
    }]
    assert merge_devices(known_devices, discovered_devices, now) == expected


def test_discover_devices_includes_new_device_discovered():
    now = datetime.utcnow()
    known_devices = [{
        "id": "1",
        "name": "first",
        DISCOVERY_TIMESTAMP_FIELD: str(now - timedelta(minutes=2)),
    }]
    discovered_devices = [{
        "id": "1",
        "name": "first",
    }, {
        "id": "2",
        "name": "second",
    }]
    expected = [{
        "id": "1",
        "name": "first",
        DISCOVERY_TIMESTAMP_FIELD: str(now - timedelta(minutes=2)),
    }, {
        "id": "2",
        "name": "second",
        DISCOVERY_TIMESTAMP_FIELD: str(now),
    }]
    assert merge_devices(known_devices, discovered_devices, now) == expected


def test_discover_devices_update_device_with_updated_fields():
    now = datetime.utcnow()
    known_devices = [{
        "id": "1",
        "name": "first",
        DISCOVERY_TIMESTAMP_FIELD: str(now - timedelta(minutes=2)),
    }]
    discovered_devices = [{
        "id": "1",
        "name": "first updated",
    }, {
        "id": "2",
        "name": "second",
    }]
    expected = [{
        "id": "1",
        "name": "first updated",
        DISCOVERY_TIMESTAMP_FIELD: str(now),
    }, {
        "id": "2",
        "name": "second",
        DISCOVERY_TIMESTAMP_FIELD: str(now),
    }]
    assert merge_devices(known_devices, discovered_devices, now) == expected


def test_discover_devices_device_that_wasnt_discovered_again_is_not_removed_from_the_devices_list():
    now = datetime.utcnow()
    known_devices = [{
        "id": "1",
        "name": "first",
        DISCOVERY_TIMESTAMP_FIELD: str(now),
    }, {
        "id": "2",
        "name": "second",
        DISCOVERY_TIMESTAMP_FIELD: str(now),
    }]
    discovered_devices = [{
        "id": "1",
        "name": "first",
    }]
    expected = known_devices
    assert merge_devices(known_devices, discovered_devices, now) == expected
