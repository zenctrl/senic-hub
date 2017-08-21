import pytest
import yaml


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


# TODO: enable testcases mocking supervisor.restart_program('nuimo_app')
# def test_delete_nuimo(browser, url_nuimo_service, settings):
#     browser.delete_json(url_nuimo_service, status=200)
#     with open(settings['nuimo_app_config_path'], 'r') as f:
#         config = yaml.load(f)
#     for mac_address in config['nuimos']:
#         assert mac_address is not '00:00:00:00:00:01'


# def test_delete_invalid_nuimo(browser, url_nuimo_not_found, settings):
#     browser.delete_json(url_nuimo_not_found, status=404)


def test_configured_nuimo(browser, url_conf, settings):
    with open(settings['nuimo_app_config_path'], 'r') as f:
        config = yaml.load(f)
    nuimos = []
    for mac_address in config['nuimos']:
        temp = config['nuimos'][mac_address]
        temp['mac_address'] = mac_address
        nuimos.append(temp)
    assert nuimos == browser.get_json(url_conf).json['nuimos']
