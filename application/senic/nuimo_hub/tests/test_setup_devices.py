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
        {"id": "ph1", "type": "philips_hue", "ip": "127.0.0.1", "authenticationRequired": True},
        {"id": "s1", "type": "sonos", "ip": "127.0.0.1", "authenticationRequired": False},
    ]


def test_devices_discover_view(tmp_device_file, browser, discover_url):
    with patch('senic.nuimo_hub.views.setup_devices.supervisor') as supervisor_mock:
        browser.post_json(discover_url, {})
        supervisor_mock.restart_program.assert_called_once_with('device_discovery')


@fixture
def auth_url(route_url):
    return route_url('devices_authenticate', device_id="ph1")


@fixture
def phue_config_path(settings):
    return os.path.join(settings["hass_phue_config_path"])


@fixture
def phue_config_file(phue_config_path):
    with open(phue_config_path, "w") as f:
        json.dump({"127.0.0.1": {"username": "23"}}, f)


@fixture
def no_phue_config_file(phue_config_path):
    if os.path.exists(phue_config_path):
        os.unlink(phue_config_path)


@responses.activate
def test_devices_authenticate_view_unauthorized(no_phue_config_file, browser, auth_url, philips_hue_bridge_description):
    payload = [{"error": {"type": PhilipsHueBridgeError.unauthorized}}]
    responses.add(responses.POST, 'http://127.0.0.1/api', json=payload, status=200)
    responses.add(responses.GET, 'http://127.0.0.1/description.xml', body=philips_hue_bridge_description, status=200)
    assert browser.post_json(auth_url, {}).json == {"id": "ph1", "authenticated": False}


@responses.activate
def test_devices_authenticate_view_returns_success(no_phue_config_file, browser, auth_url, philips_hue_bridge_description):
    payload = [{"success": {"username": "23"}}]
    responses.add(responses.POST, 'http://127.0.0.1/api', json=payload, status=200)
    responses.add(responses.GET, 'http://127.0.0.1/api/23', json={"a": 1}, status=200)
    responses.add(responses.GET, 'http://127.0.0.1/description.xml', body=philips_hue_bridge_description, status=200)
    assert browser.post_json(auth_url, {}).json == {"id": "ph1", "authenticated": True}


@responses.activate
def test_devices_authenticate_view_returns_already_authenticated(
        phue_config_file, browser, auth_url, philips_hue_bridge_description):
    responses.add(responses.GET, 'http://127.0.0.1/api/23', json={"a": 1}, status=200)
    responses.add(responses.GET, 'http://127.0.0.1/description.xml', body=philips_hue_bridge_description, status=200)
    assert browser.post_json(auth_url, {}).json == {"id": "ph1", "authenticated": True}


@responses.activate
def test_devices_authenticate_view_returns_false_if_bad_response_from_bridge(
        no_phue_config_file, browser, auth_url, philips_hue_bridge_description):
    responses.add(responses.POST, 'http://127.0.0.1/api', json={}, status=404)
    responses.add(responses.GET, 'http://127.0.0.1/description.xml', body=philips_hue_bridge_description, status=200)
    assert browser.post_json(auth_url, {}).json == {"id": "ph1", "authenticated": False}


def test_devices_authenticate_without_discovery_returns_404(no_device_file, browser, auth_url):
    assert browser.post_json(auth_url, {}, status=404)


@fixture
def bad_auth_url(route_url):
    return route_url('devices_authenticate', device_id=23)


def test_devices_authenticate_returns_404_if_device_not_found(browser, bad_auth_url):
    assert browser.post_json(bad_auth_url, {}, status=404)


@fixture
def no_auth_url(route_url):
    return route_url('devices_authenticate', device_id="s1")


def test_devices_authenticate_returns_400_when_device_doesnt_support_auth(browser, no_auth_url):
    assert browser.post_json(no_auth_url, {}, status=400)


@responses.activate
def test_devices_authenticate_try_authenticate_when_username_has_expired(
        phue_config_file, browser, auth_url, philips_hue_bridge_description):
    get_state_payload = [{"error": {"type": PhilipsHueBridgeError.unauthorized}}]
    responses.add(responses.GET, 'http://127.0.0.1/api/23', json=get_state_payload, status=200)
    auth_payload = [{"error": {"type": PhilipsHueBridgeError.button_not_pressed}}]
    responses.add(responses.POST, 'http://127.0.0.1/api', json=auth_payload, status=200)
    responses.add(responses.GET, 'http://127.0.0.1/description.xml', body=philips_hue_bridge_description, status=200)
    assert browser.post_json(auth_url, {}).json == {"id": "ph1", "authenticated": False}


@fixture
def details_url(route_url):
    return route_url('devices_details', device_id="ph1")


@responses.activate
def test_devices_details_returns_list_of_lights(
        phue_config_file, browser, details_url, philips_hue_bridge_description):
    responses.add(responses.GET, 'http://127.0.0.1/description.xml', body=philips_hue_bridge_description, status=200)
    responses.add(responses.GET, 'http://127.0.0.1/api/23/lights', json={"0": {}}, status=200)
    assert browser.get_json(details_url).json == {"0": {}}


@responses.activate
def test_devices_details_returns_502_if_philips_hue_bridge_returns_error(
        phue_config_file, browser, details_url, philips_hue_bridge_description):
    response_payload = {"error": {"type": 12345}}
    responses.add(responses.GET, 'http://127.0.0.1/api/23/lights', json=response_payload, status=200)
    responses.add(responses.GET, 'http://127.0.0.1/description.xml', body=philips_hue_bridge_description, status=200)
    assert browser.get_json(details_url, status=502)


@responses.activate
def test_devices_details_returns_502_if_philips_hue_bridge_returns_error_when_getting_description(
        phue_config_file, browser, details_url, philips_hue_bridge_description):
    responses.add(responses.GET, 'http://127.0.0.1/description.xml', status=404)
    assert browser.get_json(details_url, status=502)


@responses.activate
def test_devices_details_returns_400_if_not_authenticated(
        no_phue_config_file, browser, details_url, philips_hue_bridge_description):
    responses.add(responses.GET, 'http://127.0.0.1/description.xml', body=philips_hue_bridge_description, status=200)
    assert browser.get_json(details_url, status=400)
