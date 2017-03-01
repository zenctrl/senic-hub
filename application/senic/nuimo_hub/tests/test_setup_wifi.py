import pytest
from mock import patch


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


@pytest.yield_fixture(autouse=True)
def mocked_run(request):
    """don't run actual external commands during these tests
    """
    with patch('senic.nuimo_hub.views.setup_wifi.run')\
            as mocked_run:
        yield mocked_run


def test_join_wifi(browser, url, mocked_run, settings):
    browser.post_json(url, dict(
        ssid='grandpausethisnetwork',
        password='foobar',
        device='wlan0')).json
    mocked_run.assert_called_once_with(
        [
            '%s/join_wifi' % settings['fs_bin'],
            'grandpausethisnetwork',
            'foobar',
            'wlan0'
        ]
    )
