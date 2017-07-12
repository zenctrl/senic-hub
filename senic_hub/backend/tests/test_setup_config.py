from unittest import mock

from pytest import fixture


@fixture
def url(route_url):
    return route_url('configuration_create')


@mock.patch('senic_hub.backend.commands.supervisor.restart_program')
@mock.patch('senic_hub.backend.views.setup_config.sleep')
@mock.patch('senic_hub.backend.views.setup_config.stop_program')
def test_setup_config_returns_200_and_creates_files(
        stop_program_mock, sleep_mock, restart_program_mock,
        url, browser):
    assert browser.post_json(url, {}, status=200)
    stop_program_mock.assert_called_once_with('device_discovery')
    restart_program_mock.assert_has_calls([
        mock.call('homeassistant'),
        mock.call('nuimo_app')
    ])
