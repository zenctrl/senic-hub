import pytest
from subprocess import CalledProcessError
from unittest.mock import patch


@pytest.fixture
def setup_url(route_url):
    return route_url('wifi_setup')


def test_get_scanned_wifi(browser, setup_url):
    assert browser.get_json(setup_url).json == {'ssids': ['grandpausethisnetwork']}


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
    with patch('senic_hub.backend.views.setup_wifi.run') as mocked_run:
        yield mocked_run


@pytest.fixture
def connection_url(route_url):
    return route_url('wifi_connection')


def test_join_wifi_succeeds_with_correct_credentials(browser, connection_url, mocked_run, settings):
    browser.post_json(connection_url, dict(
        ssid='grandpausethisnetwork',
        password='foobar',
        device='wlan0')).json
    mocked_run.assert_called_once_with(
        [
            'sudo',
            '%s/join_wifi' % settings['bin_path'],
            '-c', settings['config_ini_path'],
            'grandpausethisnetwork',
            'foobar',
        ],
        check=True
    )


def test_join_wifi_enters_setup_again_if_join_fails(browser, connection_url, mocked_run, settings):
    mocked_run.side_effect = [CalledProcessError(1, ""), None]
    browser.post_json(connection_url, dict(
        ssid='grandpausethisnetwork',
        password='grandpa-forgot-correct-password',
        device='wlan0'), status=400)
    mocked_run.assert_any_call(
        [
            'sudo',
            '%s/join_wifi' % settings['bin_path'],
            '-c', settings['config_ini_path'],
            'grandpausethisnetwork',
            'grandpa-forgot-correct-password',
        ],
        check=True
    )
    mocked_run.assert_any_call(
        [
            'sudo',
            '%s/wifi_setup' % settings['bin_path'],
            '-c', settings['config_ini_path'],
            'start'
        ]
    )


def test_get_connected_wifi(browser, connection_url):
    assert browser.get_json(connection_url).json == dict(
        ssid='grandpausethisnetwork',
        status='connected'
    )


@pytest.fixture
def wifi_not_connected(settings):
    settings['joined_wifi_path'] = '/no/such/file'
    return settings


def test_get_not_connected_wifi(wifi_not_connected, browser, connection_url):
    assert browser.get_json(connection_url).json == dict(
        ssid=None,
        status='unavailable'
    )


@pytest.fixture
def adhoc_url(route_url):
    return route_url('wifi_adhoc')


def test_get_adhoc_wifi(settings, browser, adhoc_url):
    assert browser.get_json(adhoc_url).json == dict(
        ssid=settings['wifi_adhoc_ssid'],
        status='available'
    )


@pytest.fixture(scope='function')
def no_wifi_setup_mode(settings):
    settings['wifi_setup_flag_path'] = '/no/such/file'
    return settings


def test_get_no_adhoc_wifi(no_wifi_setup_mode, settings, browser, adhoc_url):
    assert browser.get_json(adhoc_url).json == dict(
        ssid=settings['wifi_adhoc_ssid'],
        status='unavailable'
    )
