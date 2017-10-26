from os import remove
from pytest import fixture, yield_fixture
from tempfile import NamedTemporaryFile

import yaml
import responses


@fixture
def nuimo_philips_hue_favourl(route_url):
    return route_url('nuimo_philips_hue_favorites', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='ph2')


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


@responses.activate
def test_get_nuimo_philips_hue_favorites_returns_nuimo_favorites(nuimo_philips_hue_favourl, browser, temporary_nuimo_app_config_file, settings):
    lights = ["4", "5", "6", "7", "8"]
    scene_dict = {
        'station1 id': {
            "name": "station1 name",
            "lights": lights
        },
        'station2 id': {
            "name": "station2 name",
            "lights": lights
        },
        'station3 id': {
            "name": "station3 name",
            "lights": lights
        }
    }

    responses.add(responses.GET, 'http://127.0.0.2/api/light_bringer/scenes', json=scene_dict, status=200)
    nuimo_favorites = browser.get(nuimo_philips_hue_favourl, status=200).json

    assert nuimo_favorites['station1'] == {"id": "station1 id", "name": "station1 name"}
    assert nuimo_favorites['station2'] == {"id": "station2 id", "name": "station2 name"}
    assert nuimo_favorites['station3'] == {"id": "station3 id", "name": "station3 name"}


@responses.activate
def test_get_nuimo_philips_hue_favorites_returns_None(nuimo_philips_hue_favourl, browser, temporary_nuimo_app_config_file, settings):
    lights = ["5", "6", "7", "8"]
    scene_dict = {
        'station1 id': {
            "name": "station1 name",
            "lights": lights
        },
        'station2 id': {
            "name": "station2 name",
            "lights": lights
        },
        'station3 id': {
            "name": "station3 name",
            "lights": lights
        }
    }

    responses.add(responses.GET, 'http://127.0.0.2/api/light_bringer/scenes', json=scene_dict, status=200)
    nuimo_favorites = browser.get(nuimo_philips_hue_favourl, status=200).json

    assert nuimo_favorites['station1'] is None
    assert nuimo_favorites['station2'] is None
    assert nuimo_favorites['station3'] is None


def test_get_nuimo_philips_hue_favorites_returns_ConnectionError(nuimo_philips_hue_favourl, browser, temporary_nuimo_app_config_file, settings):

    nuimo_favorites = browser.get(nuimo_philips_hue_favourl).json

    assert nuimo_favorites['station1'] is None
    assert nuimo_favorites['station2'] is None
    assert nuimo_favorites['station3'] is None


@responses.activate
def test_get_nuimo_philips_hue_favorites_not_in_configuration_file_returns_nuimo_favorites(nuimo_philips_hue_favourl, browser, temporary_nuimo_app_config_file, settings):

    with open(settings['nuimo_app_config_path'], 'r+') as f:
        config = yaml.load(f)
        del config['nuimos']['00:00:00:00:00:00']['components'][0]['station1']
        del config['nuimos']['00:00:00:00:00:00']['components'][0]['station2']
        del config['nuimos']['00:00:00:00:00:00']['components'][0]['station3']
        f.seek(0)  # We want to overwrite the config file with the new configuration
        f.truncate()
        yaml.dump(config, f, default_flow_style=False)

    lights = ["4", "5", "6", "7", "8"]
    scene_dict = {
        'a': {
            "name": "Nightlight",
            "lights": lights
        },
        'b': {
            "name": "Relax",
            "lights": lights
        },
        'c': {
            "name": "Concentrate",
            "lights": lights
        }
    }

    responses.add(responses.GET, 'http://127.0.0.2/api/light_bringer/scenes', json=scene_dict, status=200)
    nuimo_favorites = browser.get(nuimo_philips_hue_favourl, status=200).json

    assert nuimo_favorites['station1']['name'] in ["Nightlight", "Relax", "Concentrate"]
    assert nuimo_favorites['station2']['name'] in ["Nightlight", "Relax", "Concentrate"]
    assert nuimo_favorites['station3']['name'] in ["Nightlight", "Relax", "Concentrate"]


def test_get_nuimo_philips_hue_favorites_not_in_configuration_file_ConnectionError(nuimo_philips_hue_favourl, browser, temporary_nuimo_app_config_file, settings):

    with open(settings['nuimo_app_config_path'], 'r+') as f:
        config = yaml.load(f)
        del config['nuimos']['00:00:00:00:00:00']['components'][0]['station1']
        del config['nuimos']['00:00:00:00:00:00']['components'][0]['station2']
        del config['nuimos']['00:00:00:00:00:00']['components'][0]['station3']
        f.seek(0)  # We want to overwrite the config file with the new configuration
        f.truncate()
        yaml.dump(config, f, default_flow_style=False)

    nuimo_favorites = browser.get(nuimo_philips_hue_favourl, status=200).json

    assert nuimo_favorites['station1'] is None
    assert nuimo_favorites['station2'] is None
    assert nuimo_favorites['station3'] is None


def test_get_nuimo_philips_hue_favorites_for_invalid_component_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.get(route_url('nuimo_philips_hue_favorites', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='invalid-id'), status=404)


def test_get_nuimo_philips_hue_favorites_for_invalid_nuimo_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.get(route_url('nuimo_philips_hue_favorites', mac_address='de:ad:be:ef:00:00'.replace(':', '-'), component_id='ph2'), status=404)


def test_get_nuimo_philips_hue_favorites_for_wrong_component_type_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.get(route_url('nuimo_philips_hue_favorites', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='s1'), status=404)


def test_put_nuimo_philips_hue_favorites(nuimo_philips_hue_favourl, browser, temporary_nuimo_app_config_file, settings):
    browser.put_json(nuimo_philips_hue_favourl, {
        "number": 1,
        "item": {
            "id": "station1 new id",
            "name": "station1 new name"
        }
    }, status=200)

    with open(settings['nuimo_app_config_path'], 'r') as f:
        config = yaml.load(f)

    component = next(c for c in config['nuimos']['00:00:00:00:00:00']['components'] if c['id'] == 'ph2')
    assert set(component['station1']) == set({
        "id": "station1 new id",
        "name": "station1 new name"
    })


def test_put_nuimo_philips_hue_favorites_for_invalid_component_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.put_json(route_url('nuimo_philips_hue_favorites', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='invalid-id'), {
        "number": 1,
        "item": {
            "id": "station1 new id",
            "name": "station1 new name"
        }
    }, status=404)


def test_put_nuimo_philips_hue_favorites_for_invalid_nuimo_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.put_json(route_url('nuimo_philips_hue_favorites', mac_address='de:ad:be:ef:00:00'.replace(':', '-'), component_id='ph2'), {
        "number": 1,
        "item": {
            "id": "station1 new id",
            "name": "station1 new name"
        }
    }, status=404)


def test_put_nuimo_philips_hue_favorites_for_wrong_component_type_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.put_json(route_url('nuimo_philips_hue_favorites', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='s1'), {
        "number": 1,
        "item": {
            "id": "station1 new id",
            "name": "station1 new name"
        }
    }, status=404)
