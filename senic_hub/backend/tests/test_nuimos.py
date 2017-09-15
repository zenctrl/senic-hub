import pytest
# import yaml


@pytest.fixture
def url(route_url):
    return route_url('connected_nuimos')


@pytest.fixture
def url_conf(route_url):
    return route_url('configured_nuimos')


@pytest.fixture
def url_nuimo_service(route_url):
    return route_url('nuimo_services', mac_address='00:00:00:00:00:01'.replace(':', '-'))


@pytest.fixture
def url_nuimo_not_found(route_url):
    return route_url('nuimo_services', mac_address='00:00:00:00:00:02'.replace(':', '-'))


def test_returns_nuimo(browser, url):
    assert browser.get_json(url).json['nuimos'] == ['AA-BB-CC-DD-EE-FF']


@pytest.fixture
def no_such_nuimo(settings):
    settings['nuimo_mac_address_filepath'] = '/no/such/file'
    return settings


def test_returns_no_nuimo(no_such_nuimo, browser, url):
    assert browser.get_json(url).json == {'nuimos': []}
