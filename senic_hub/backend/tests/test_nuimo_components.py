from configparser import ConfigParser
from os import remove
from pytest import fixture, yield_fixture
from tempfile import NamedTemporaryFile

from senic_hub.backend.views.nuimo_components import create_component


@fixture
def url(route_url):
    return route_url('nuimo_components', nuimo_id=0)


@fixture
def no_nuimo_app_config_file(settings):
    settings['nuimo_app_config_path'] = '/no/such/file'
    return settings


def test_nuimo_components_returns_404_if_config_file_doesnt_exist(
        no_nuimo_app_config_file, url, browser):
    assert browser.get_json(url, status=404)


def test_nuimo_components_returns_components(url, browser):
    assert browser.get_json(url).json == {'components': [
        {'component': 'philips_hue', 'device_id': 'ph2', 'selected_devices': ['5', '7', '4', '8', '6']},
        {'component': 'media_player', 'device_id': 'soundtouch1'},
        {'component': 'sonos', 'device_id': 's1'},
    ]}


@yield_fixture(autouse=True)
def temporary_nuimo_app_config_file(settings):
    """don't run actual external commands during these tests
    """
    with NamedTemporaryFile('w+', delete=False) as f:
        temp_file_name = f.name
        with open(settings['nuimo_app_config_path']) as config_file:
            f.write(config_file.read())
    settings['nuimo_app_config_path'] = f.name
    yield temporary_nuimo_app_config_file
    remove(temp_file_name)


def test_add_component_returns_adds_it_to_components(url, browser, temporary_nuimo_app_config_file, settings):
    browser.post_json(url, {
        'device_id': 's1',
        'component': 'sonos'},
        status=200
    )

    config = ConfigParser()
    config.read(settings['nuimo_app_config_path'])
    assert len(config.sections()) == 4
    last_section = dict(config.items(config.sections()[-1]))
    assert last_section['device_id'] == 's1'
    assert last_section['ip_address'] == '127.0.0.1'
    assert last_section['component'] == 'sonos'


def test_add_component_returns_new_component(url, browser):
    response = browser.post_json(url, {
        'device_id': 's1',
        'component': 'sonos'}
    ).json
    assert 'id' in response
    assert response['device_id'] == 's1'
    assert response['component'] == 'sonos'
    assert response['ip_address'] == '127.0.0.1'
    assert response['index'] == 3


def test_adding_compontent_with_unknown_device_id_returns_400(url, browser, temporary_nuimo_app_config_file):
    browser.post_json(url, {
        'device_id': 'invalid-device-id',
        'component': 'sonos'},
        status=400
    )


def test_create_philips_hue_component():
    device = {
        'id': 'ph1',
        'type': 'philips_hue',
        'ip': '127.0.0.1',
        'extra': {
            'username': 'light_bringer',
            'lights': {
                '4': {},
                '5': {},
                '6': {},
                '7': {},
                '8': {},
            }
        }
    }
    component = create_component(device)
    assert component == {
        'id': component['id'],
        'device_id': 'ph1',
        'component': 'philips_hue',
        'ip_address': '127.0.0.1',
        'username': 'light_bringer',
        'lights': '4, 5, 6, 7, 8'
    }


def test_create_soundtouch_component():
    device = {
        'id': 'soundtouch1',
        'type': 'soundtouch'
    }
    component = create_component(device)
    assert component == {
        'id': component['id'],
        'device_id': 'soundtouch1',
        'component': 'media_player'
    }


@fixture
def component_url(route_url):
    return route_url('nuimo_component', nuimo_id=0, component_id='component-ph2')


def test_delete_component_returns_200(component_url, browser, temporary_nuimo_app_config_file, settings):
    browser.delete(component_url, status=200)
    with open(settings['nuimo_app_config_path'], 'r+') as f:
        config = ConfigParser()
        config.read_file(f)
        assert len(config.sections()) == 2
        assert component_url.rsplit('/', 1)[-1] not in config.sections()


def test_delete_invalid_component_returns_404(route_url, browser, temporary_nuimo_app_config_file):
    browser.delete(route_url('nuimo_component', nuimo_id=0, component_id='invalid-id'), status=404)
