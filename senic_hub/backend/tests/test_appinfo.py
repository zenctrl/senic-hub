import pytest


@pytest.fixture
def url(route_url):
    return route_url('appinfo')


def test_appinfo_version(url, browser):
    assert 'version' in browser.get_json(url).json
