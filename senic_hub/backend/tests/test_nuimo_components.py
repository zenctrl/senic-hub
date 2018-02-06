from os import remove
from pytest import fixture, yield_fixture
from tempfile import NamedTemporaryFile

import yaml
import responses

from senic_hub.backend.views.nuimo_components import create_component


@fixture
def url(route_url):
    return route_url('nuimo_components', mac_address='00:00:00:00:00:00'.replace(':', '-'))


@fixture
def no_such_nuimo_url(route_url):
    return route_url('nuimo_components', mac_address='de:ad:be:ef:00:00'.replace(':', '-'))


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
            'id': 'ph2',
            'type': 'philips_hue',
            'device_ids': ['ph2-light-4', 'ph2-light-5', 'ph2-light-6', 'ph2-light-7', 'ph2-light-8'],
            'name': "Philips Hue Bridge 2"
        },
        {
            'id': 's1',
            'type': 'sonos',
            'device_ids': ['s1'],
            'name': "Sonos Player S1"
        }
    ]}


def test_nuimo_components_returns_404_if_nuimo_doesnt_exist(no_such_nuimo_url, browser):
    assert browser.get_json(no_such_nuimo_url, status=404)


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
    with open(settings['nuimo_app_config_path'], 'r') as f:
        config = yaml.load(f)

    components = config['nuimos']['00:00:00:00:00:00']['components']
    assert len(components) == 3
    added_component = components[len(components) - 1]
    assert 'id' in added_component
    assert added_component['device_ids'] == ['s1']
    assert added_component['ip_address'] == '127.0.0.1'
    assert added_component['type'] == 'sonos'


def test_add_component_returns_new_component(url, browser, temporary_nuimo_app_config_file):
    response = browser.post_json(url, {'device_ids': ['ph2-light-4']}).json
    assert 'id' in response
    assert response['device_ids'] == ['ph2-light-4']
    assert response['type'] == 'philips_hue'
    assert response['ip_address'] == '127.0.0.2'


def test_adding_component_with_unknown_device_id_returns_400(url, browser, temporary_nuimo_app_config_file):
    browser.post_json(url, {'device_ids': ['invalid-device-id']}, status=400)


def test_adding_component_with_unknown_nuimo_returns_404(
        no_such_nuimo_url, browser):
    assert browser.post_json(no_such_nuimo_url, {
        'device_ids': ['s1'],
        'type': 'sonos'},
        status=404)


def test_create_philips_hue_component():
    device = {
        'id': 'ph1',
        'type': 'philips_hue',
        'name': 'Philips Hue Bridge 1',
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
        'name': 'Philips Hue Bridge 1',
        'ip_address': '127.0.0.1',
        'username': 'light_bringer',
    }


def test_create_sonos_component():
    device = {
        'id': 'sonos1',
        'type': 'sonos',
        'name': 'test sonos',
        'ip': '127.0.0.1',
        'extra': {}
    }
    component = create_component(device)
    assert component == {
        'id': component['id'],
        'device_ids': ['sonos1'],
        'type': 'sonos',
        'name': 'test sonos',
        'ip_address': '127.0.0.1',
    }


@fixture
def component_url(route_url):
    return route_url('nuimo_component', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='ph2')


def test_get_component_returns_component(component_url, browser, temporary_nuimo_app_config_file, settings):
    component = browser.get(component_url, status=200).json
    component_id = component_url.rsplit('/', 1)[-1]
    assert component == {
        'id': component_id,
        'device_ids': ['ph2-light-4', 'ph2-light-5', 'ph2-light-6', 'ph2-light-7', 'ph2-light-8'],
        'type': 'philips_hue',
        'name': 'Philips Hue Bridge 2',
        'ip_address': '127.0.0.2',
        'username': 'light_bringer',
        'station1': {
            "name": "station1 name"
        },
        'station2': {
            "name": "station2 name"
        },
        'station3': {
            "name": "station3 name"
        }
    }


def test_get_invalid_component_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.get(route_url('nuimo_component', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='invalid-id'), status=404)


def test_get_component_of_unknown_nuimo_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.get(route_url('nuimo_component', mac_address='de:ad:be:ef:00:00'.replace(':', '-'), component_id='ph2'), status=404)


def test_delete_component_returns_200(component_url, browser, temporary_nuimo_app_config_file, settings):
    browser.delete(component_url, status=200)
    component_id = component_url.rsplit('/', 1)[-1]
    with open(settings['nuimo_app_config_path'], 'r') as f:
        config = yaml.load(f)

    components = config['nuimos']['00:00:00:00:00:00']['components']
    assert len(components) == 1
    for component in config['nuimos']['00:00:00:00:00:00']['components']:
        assert component_id is not component['id']


def test_delete_invalid_component_returns_404(route_url, browser, temporary_nuimo_app_config_file):
    browser.delete(route_url('nuimo_component', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='invalid-id'), status=404)


def test_delete_component_of_unknown_nuimo_returns_404(route_url, browser, temporary_nuimo_app_config_file):
    browser.delete(route_url('nuimo_component', mac_address='de:ad:be:ef:00:00'.replace(':', '-'), component_id='ph2'), status=404)


def test_put_invalid_component_returns_404(route_url, browser, temporary_nuimo_app_config_file):
    browser.put_json(
        route_url('nuimo_component', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='invalid-id'),
        {'device_ids': ['device-id']},
        status=404)


def test_put_component_devices_modifies_app_config(component_url, browser, temporary_nuimo_app_config_file, settings):
    browser.put_json(component_url, {'device_ids': ['ph2-light-5', 'ph2-light-6']}, status=200)

    with open(settings['nuimo_app_config_path'], 'r') as f:
        config = yaml.load(f)

    component = next(c for c in config['nuimos']['00:00:00:00:00:00']['components'] if c['id'] == 'ph2')
    assert set(component['device_ids']) == set(['ph2-light-5', 'ph2-light-6'])


def test_put_component_devices_returns_modified_component(component_url, browser):
    response = browser.put_json(component_url, {'device_ids': ['ph2-light-5', 'ph2-light-6']}).json
    component_id = component_url.rsplit('/', 1)[-1]

    assert response['id'] == component_id
    assert set(response['device_ids']) == set(['ph2-light-5', 'ph2-light-6'])


def test_put_component_devices_of_unknown_nuimo_returns_404(route_url, browser):
    browser.put_json(
        route_url('nuimo_component', mac_address='de:ad:be:ef:00:00'.replace(':', '-'), component_id='ph2'),
        {'device_ids': ['ph2-light-5']},
        status=404)


@fixture
def device_test_url(route_url):
    return route_url('nuimo_device_test', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='ph2', device_id='ph2-light-5')


def test_get_invalid_device_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.get(route_url('nuimo_device_test', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='ph2', device_id='invalid_device-id'), status=404)


def test_get_device_test_fail_message(device_test_url, browser, temporary_nuimo_app_config_file):
    device = browser.get(device_test_url, status=200).json
    device_id = device_test_url.rsplit('/')[-1]
    assert device == {
        'test_component': 'philips_hue',
        'test_component_id': 'ph2',
        'test_device_id': str(device_id),
        'test_result': 'FAIL',
        'message': 'ERROR_PHUE_PUT_REQUEST_FAIL'
    }


@responses.activate
def test_get_device_test_pass_message(device_test_url, browser, temporary_nuimo_app_config_file):

    state = {'state': {'on': True, 'bri': 30}}

    responses.add(responses.GET, 'http://127.0.0.2/api/light_bringer/lights/5', json=state, status=200)
    responses.add(responses.PUT, 'http://127.0.0.2/api/light_bringer/lights/5/state', json={}, status=200)
    device = browser.get(device_test_url, status=200).json
    device_id = device_test_url.rsplit('/')[-1]
    assert device == {
        'test_component': 'philips_hue',
        'test_component_id': 'ph2',
        'test_device_id': str(device_id),
        'test_result': 'PASS',
        'message': 'BLINK_SUCCESSFUL'
    }


@responses.activate
def test_get_device_test_fail_message_due_to_put_exception(device_test_url, browser, temporary_nuimo_app_config_file):

    state = {'state': {'on': True, 'bri': 30}}

    responses.add(responses.GET, 'http://127.0.0.2/api/light_bringer/lights/5', json=state, status=200)
    device = browser.get(device_test_url, status=200).json
    device_id = device_test_url.rsplit('/')[-1]
    assert device == {
        'test_component': 'philips_hue',
        'test_component_id': 'ph2',
        'test_device_id': str(device_id),
        'test_result': 'FAIL',
        'message': 'ERROR_PHUE_PUT_REQUEST_FAIL'
    }


def test_get_component_of_unknown_nuimo_test_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.get(route_url('nuimo_device_test', mac_address='de:ad:be:ef:00:00'.replace(':', '-'), component_id='ph2', device_id='ph2-light-5'), status=404)


def test_get_invalid_component_test_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.get(route_url('nuimo_device_test', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='invalid-id-1', device_id='ph2-light-5'), status=404)
