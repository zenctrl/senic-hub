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
        {
            'id': 'component-ph2',
            'type': 'philips_hue',
            'device_ids': ['ph2-light-4', 'ph2-light-5', 'ph2-light-6', 'ph2-light-7', 'ph2-light-8'],
        },
        {
            'id': 'component-soundtouch1',
            'type': 'media_player',
            'device_ids': ['soundtouch1'],
        },
        {
            'id': 'component-s1',
            'type': 'sonos',
            'device_ids': ['s1'],
        },
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


def test_add_component_adds_to_app_config(url, browser, temporary_nuimo_app_config_file, settings):
    browser.post_json(url, {
        'device_ids': ['s1'],
        'type': 'sonos'},
        status=200
    )

    config = ConfigParser()
    config.read(settings['nuimo_app_config_path'])
    assert len(config.sections()) == 4
    last_section = dict(config.items(config.sections()[-1]))
    assert last_section['device_ids'] == ', '.join(['s1'])
    assert last_section['ip_address'] == '127.0.0.1'
    assert last_section['type'] == 'sonos'


def test_add_component_returns_new_component(url, browser, temporary_nuimo_app_config_file):
    response = browser.post_json(url, {'device_ids': ['ph2-light-4']}).json
    assert 'id' in response
    assert response['device_ids'] == ['ph2-light-4']
    assert response['type'] == 'philips_hue'
    assert response['ip_address'] == '127.0.0.2'
    assert response['index'] == 3


def test_adding_component_with_unknown_device_id_returns_400(url, browser, temporary_nuimo_app_config_file):
    browser.post_json(url, {'device_ids': ['invalid-device-id']}, status=400)


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
        'device_ids': ['ph1-light-4', 'ph1-light-5', 'ph1-light-6', 'ph1-light-7', 'ph1-light-8'],
        'type': 'philips_hue',
        'ip_address': '127.0.0.1',
        'username': 'light_bringer',
    }


def test_create_soundtouch_component():
    device = {
        'id': 'soundtouch1',
        'type': 'soundtouch',
        'ha_entity_id': 'media_player.bose_soundtouch',
    }
    component = create_component(device)
    assert component == {
        'id': component['id'],
        'device_ids': ['soundtouch1'],
        'type': 'media_player',
        'ha_entity_id': 'media_player.bose_soundtouch',
    }


@fixture
def component_url(route_url):
    return route_url('nuimo_component', nuimo_id=0, component_id='component-ph2')


def test_get_component_returns_component(component_url, browser, temporary_nuimo_app_config_file, settings):
    component = browser.get(component_url, status=200).json
    component_id = component_url.rsplit('/', 1)[-1]
    assert component == {
        'id': component_id,
        'device_ids': ['ph2-light-4', 'ph2-light-5', 'ph2-light-6', 'ph2-light-7', 'ph2-light-8'],
        'type': 'philips_hue',
        'ip_address': '127.0.0.2',
        'username': 'light_bringer',
    }


def test_get_invalid_component_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.get(route_url('nuimo_component', nuimo_id=0, component_id='invalid-id'), status=404)


def test_delete_component_returns_200(component_url, browser, temporary_nuimo_app_config_file, settings):
    browser.delete(component_url, status=200)
    component_id = component_url.rsplit('/', 1)[-1]
    with open(settings['nuimo_app_config_path'], 'r+') as f:
        config = ConfigParser()
        config.read_file(f)
        assert len(config.sections()) == 2
        assert component_id not in config.sections()


def test_delete_invalid_component_returns_404(route_url, browser, temporary_nuimo_app_config_file):
    browser.delete(route_url('nuimo_component', nuimo_id=0, component_id='invalid-id'), status=404)


def test_put_invalid_component_returns_404(route_url, browser, temporary_nuimo_app_config_file):
    browser.put_json(
        route_url('nuimo_component', nuimo_id=0, component_id='invalid-id'),
        {'device_ids': ['device-id']},
        status=404)


def test_put_component_devices_modifies_app_config(component_url, browser, temporary_nuimo_app_config_file, settings):
    browser.put_json(component_url, {'device_ids': ['ph2-light-5', 'ph2-light-6']}, status=200)

    config = ConfigParser()
    config.read(settings['nuimo_app_config_path'])
    component = dict(config['component-ph2'])
    assert set(component['device_ids'].split(', ')) == set(['ph2-light-5', 'ph2-light-6'])


def test_put_component_devices_returns_modified_component(component_url, browser):
    response = browser.put_json(component_url, {'device_ids': ['ph2-light-5', 'ph2-light-6']}).json
    component_id = component_url.rsplit('/', 1)[-1]
    assert response['id'] == component_id
    assert set(response['device_ids']) == set(['ph2-light-5', 'ph2-light-6'])
