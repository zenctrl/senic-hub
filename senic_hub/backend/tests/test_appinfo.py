import pytest

from pytest import fixture


@pytest.fixture
def url(route_url):
    return route_url('appinfo')


def test_appinfo_version(url, browser):
    assert 'version' in browser.get_json(url).json


@fixture
def without_hub_config_files(settings):
    settings['nuimo_app_config_path'] = '/no/such/file'
    settings['devices_path'] = '/no/such/file'
    settings['homeassistant_config_path'] = '/no/such/file'
    return settings


def test_appinfo_returns_not_onboarded_if_config_files_are_missing(without_hub_config_files, url, browser):
    assert not browser.get_json(url).json['onboarded']


def test_appinfo_returns_onboarded_if_all_files_exists(url, browser):
    assert browser.get_json(url).json['onboarded']
