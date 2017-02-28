import pytest


@pytest.fixture
def url(route_url):
    return route_url('wifi_setup')


def test_get_scanned_wifi(browser, url):
    assert browser.get_json(url).json['grandpausethisnetwork']['device'] == "wlan0"


@pytest.fixture
def no_such_wifi(settings):
    settings['fs_wifi_networks'] = '/no/such/file'
    return settings


def test_get_scanned_wifi_empty(no_such_wifi, browser, url):
    assert browser.get_json(url).json == {}
