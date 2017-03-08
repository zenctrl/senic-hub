import pytest
from mock import patch


@pytest.fixture
def setup_url(route_url):
    return route_url('wifi_setup')


def test_get_scanned_wifi(browser, setup_url):
    assert browser.get_json(setup_url).json == ['grandpausethisnetwork']


@pytest.fixture
def no_such_wifi(settings):
    settings['wifi_networks_path'] = '/no/such/file'
    return settings


def test_get_scanned_wifi_empty(no_such_wifi, browser, setup_url):
    assert browser.get_json(setup_url).json == []


@pytest.yield_fixture(autouse=True)
def mocked_run(request):
    """don't run actual external commands during these tests
    """
    with patch('senic.nuimo_hub.views.setup_wifi.run')\
            as mocked_run:
        yield mocked_run


def test_join_wifi(browser, setup_url, mocked_run, settings):
    browser.post_json(setup_url, dict(
        ssid='grandpausethisnetwork',
        password='foobar',
        device='wlan0')).json
    mocked_run.assert_called_once_with(
        [
            'sudo',
            '%s/join_wifi' % settings['bin_path'],
            '-c {fs_config_ini}'.format(**settings),
            'grandpausethisnetwork',
            'foobar',
        ]
    )
