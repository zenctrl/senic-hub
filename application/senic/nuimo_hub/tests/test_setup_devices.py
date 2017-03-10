import json
import os
import os.path

from tempfile import mktemp
from unittest.mock import patch

from pytest import fixture

import responses

from senic.nuimo_hub.device_discovery import PhilipsHueBridgeError


@fixture
def url(route_url):
    return route_url('devices_list')


@fixture
def discover_url(route_url):
    return route_url('devices_discover')


@fixture
def no_device_file(settings):
    settings['devices_path'] = '/no/such/file'
    return settings


@fixture
def tmp_device_file(settings):
    settings['devices_path'] = mktemp()
    return settings


def test_device_list_is_empty_if_devices_file_doesnt_exist(no_device_file, browser, url):
    assert browser.get_json(url).json == []


def test_device_list_contains_devices(browser, url):
    assert browser.get_json(url).json == [
        {"id": 0, "type": "philips_hue", "ip": "127.0.0.1"},
        {"id": 1, "type": "sonos", "ip": "127.0.0.1"},
    ]


def test_devices_discover_view(tmp_device_file, browser, discover_url):
    with patch('senic.nuimo_hub.views.setup_devices.discover') as discover_mock:
        discover_mock.return_value = []
        assert browser.post_json(discover_url, {}).json == []


@fixture
def auth_url(route_url):
    return route_url('devices_authenticate', device_id=0)


@fixture
def state_file_path(settings):
    return os.path.join(settings["data_path"], "127.0.0.1")


@fixture
def state_file(state_file_path):
    with open(state_file_path, "w") as f:
        json.dump({"devicetype": "", "username": 23}, f)


@fixture
def no_state_file(state_file_path):
    if os.path.exists(state_file_path):
        os.unlink(state_file_path)


@responses.activate
def test_devices_authenticate_view_unauthorized(no_state_file, browser, auth_url):
    payload = [{"error": {"type": PhilipsHueBridgeError.unauthorized}}]
    responses.add(responses.POST, 'http://127.0.0.1/api', json=payload, status=200)
    assert browser.post_json(auth_url, {}).json == {"id": 0, "authenticated": False}


@responses.activate
def test_devices_authenticate_view_returns_success(no_state_file, browser, auth_url):
    payload = [{"success": {"username": "23"}}]
    responses.add(responses.POST, 'http://127.0.0.1/api', json=payload, status=200)
    responses.add(responses.GET, 'http://127.0.0.1/api/23', json={"a": 1}, status=200)
    assert browser.post_json(auth_url, {}).json == {"id": 0, "authenticated": True}


@responses.activate
def test_devices_authenticate_view_returns_already_authenticated(state_file, browser, auth_url):
    responses.add(responses.GET, 'http://127.0.0.1/api/23', json={"a": 1}, status=200)
    assert browser.post_json(auth_url, {}).json == {"id": 0, "authenticated": True}


@responses.activate
def test_devices_authenticate_view_returns_false_if_bad_response_from_bridge(no_state_file, browser, auth_url):
    responses.add(responses.POST, 'http://127.0.0.1/api', json={}, status=404)
    assert browser.post_json(auth_url, {}).json == {"id": 0, "authenticated": False}


def test_devices_authenticate_without_discovery_returns_404(no_device_file, browser, auth_url):
    assert browser.post_json(auth_url, {}, status=404)


@fixture
def bad_auth_url(route_url):
    return route_url('devices_authenticate', device_id=23)


def test_devices_authenticate_returns_404_if_device_not_found(browser, bad_auth_url):
    assert browser.post_json(bad_auth_url, {}, status=404)


@fixture
def no_auth_url(route_url):
    return route_url('devices_authenticate', device_id=1)


def test_devices_authenticate_returns_400_when_device_doesnt_support_auth(browser, no_auth_url):
    assert browser.post_json(no_auth_url, {}, status=400)


@responses.activate
def test_devices_authenticate_try_authenticate_when_username_has_expired(state_file, browser, auth_url):
    get_state_payload = [{"error": {"type": PhilipsHueBridgeError.unauthorized}}]
    responses.add(responses.GET, 'http://127.0.0.1/api/23', json=get_state_payload, status=200)
    responses.add(responses.POST, 'http://127.0.0.1/api', json=[{"error": {}}], status=200)
    assert browser.post_json(auth_url, {}).json == {"id": 0, "authenticated": False}


@fixture
def details_url(route_url):
    return route_url('devices_details', device_id=0)


@responses.activate
def test_devices_details_returns_list_of_lights(state_file, browser, details_url):
    responses.add(responses.GET, 'http://127.0.0.1/api/23/lights', json={"0": {}}, status=200)
    assert browser.get_json(details_url).json == {"0": {}}


@responses.activate
def test_devices_details_returns_400_if_not_authenticated(no_state_file, browser, details_url):
    assert browser.get_json(details_url, status=400)
