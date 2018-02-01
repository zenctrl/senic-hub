import pytest


@pytest.fixture
def url(route_url):
    return route_url('appinfo')


def test_appinfo_completeness(url, browser):
    app_info = browser.get_json(url).json
    assert 'wifi' in app_info
    assert 'os_version' in app_info
    assert 'hardware_identifier' in app_info
