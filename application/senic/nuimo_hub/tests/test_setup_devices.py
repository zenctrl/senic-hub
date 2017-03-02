from tempfile import mktemp
from unittest.mock import patch

from pytest import fixture


@fixture
def url(route_url):
    return route_url('devices_list')


@fixture
def discover_url(route_url):
    return route_url('devices_discover')


@fixture
def no_device_file(settings):
    settings['fs_device_list'] = '/no/such/file'
    return settings


@fixture
def tmp_device_file(settings):
    settings['fs_device_list'] = mktemp()
    return settings


def test_device_list_file_doesnt_exist(no_device_file, browser, url):
    assert browser.get_json(url).json == {}


def test_device_list(browser, url):
    assert browser.get_json(url).json == {"id": 0, "type": "philips_hue", "ip": "127.0.0.1"}


def test_devices_discover_view(tmp_device_file, browser, discover_url):
    with patch('senic.nuimo_hub.views.setup_devices.discover') as discover_mock:
        discover_mock.return_value = []
        assert browser.post_json(discover_url, {}).json == []
