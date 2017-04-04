import pytest
from collections import namedtuple
from subprocess import CalledProcessError, TimeoutExpired
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


def test_join_wifi_returns_200_when_join_succeeds(browser, connection_url, mocked_run, settings):
    browser.post_json(connection_url, dict(
        ssid='grandpausethisnetwork',
        password='foobar'))
    mocked_run.assert_any_call(
        [
            'sudo',
            '%s/wifi_setup' % settings['bin_path'],
            '-c', settings['config_ini_path'],
            'join',
            'grandpausethisnetwork',
            'foobar',
        ], check=True
    )


def test_join_wifi_returns_400_when_join_fails(browser, connection_url, mocked_run, settings):
    mocked_run.side_effect = [CalledProcessError(1, None)]
    browser.post_json(connection_url, dict(
        ssid='grandpausethisnetwork',
        password='foobar'), status=400)
    mocked_run.assert_any_call(
        [
            'sudo',
            '%s/wifi_setup' % settings['bin_path'],
            '-c', settings['config_ini_path'],
            'join',
            'grandpausethisnetwork',
            'foobar',
        ], check=True
    )


def test_connection_status_returns_connected_if_wifi_is_connected(browser, connection_url, mocked_run):
    Output = namedtuple('Output', ['stdout'])
    mocked_run.side_effect = [Output(stdout=b"infra_ssid=grandpausethisnetwork\ninfra_status=connected")]
    assert browser.get_json(connection_url).json == dict(
        ssid='grandpausethisnetwork',
        status='connected'
    )


def test_connection_status_returns_connecting_if_wifi_is_connected(browser, connection_url, mocked_run):
    Output = namedtuple('Output', ['stdout'])
    mocked_run.side_effect = [Output(stdout=b"infra_ssid=grandpausethisnetwork\ninfra_status=connecting")]
    assert browser.get_json(connection_url).json == dict(
        ssid='grandpausethisnetwork',
        status='connecting'
    )


def test_connection_status_returns_unavailable_if_wifi_is_not_connected(browser, connection_url, mocked_run):
    Output = namedtuple('Output', ['stdout'])
    mocked_run.side_effect = [Output(stdout=b"")]
    assert browser.get_json(connection_url).json == dict(
        ssid=None,
        status='unavailable'
    )


def test_connection_status_returns_unavailable_if_retrieving_status_takes_too_long(browser, connection_url, mocked_run):
    mocked_run.side_effect = [TimeoutExpired(None, None)]
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
