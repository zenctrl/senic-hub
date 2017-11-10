from os import remove
from pytest import fixture, yield_fixture
from tempfile import NamedTemporaryFile

import yaml


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


def test_get_nuimo_philips_hue_favorites_returns_nuimo_favorites(nuimo_philips_hue_favourl, browser, temporary_nuimo_app_config_file, settings):
    nuimo_favorites = browser.get(nuimo_philips_hue_favourl, status=200).json

    assert set(nuimo_favorites) == set({
        'station1': {
            "name": "station1 name"
        },
        'station2': {
            "name": "station2 name"
        },
        'station3': {
            "name": "station3 name"
        }
    })


def test_get_nuimo_philips_hue_favorites_for_invalid_component_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.get(route_url('nuimo_philips_hue_favorites', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='invalid-id'), status=404)


def test_get_nuimo_philips_hue_favorites_for_invalid_nuimo_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.get(route_url('nuimo_philips_hue_favorites', mac_address='de:ad:be:ef:00:00'.replace(':', '-'), component_id='ph2'), status=404)


def test_get_nuimo_philips_hue_favorites_for_wrong_component_type_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.get(route_url('nuimo_philips_hue_favorites', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='s1'), status=404)


def test_put_nuimo_philips_hue_favorites(nuimo_philips_hue_favourl, browser, temporary_nuimo_app_config_file, settings):
    browser.put_json(nuimo_philips_hue_favourl, {
        "number": 1,
        "name": "station1 new name"
    }, status=200)

    with open(settings['nuimo_app_config_path'], 'r') as f:
        config = yaml.load(f)

    component = next(c for c in config['nuimos']['00:00:00:00:00:00']['components'] if c['id'] == 'ph2')
    assert component['station1']['name'] == "station1 new name"


def test_put_nuimo_philips_hue_favorites_for_invalid_component_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.put_json(route_url('nuimo_philips_hue_favorites', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='invalid-id'), {
        "number": 1,
        "name": "station1 new name"
    }, status=404)


def test_put_nuimo_philips_hue_favorites_for_invalid_nuimo_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.put_json(route_url('nuimo_philips_hue_favorites', mac_address='de:ad:be:ef:00:00'.replace(':', '-'), component_id='ph2'), {
        "number": 1,
        "name": "station1 new name"
    }, status=404)


def test_put_nuimo_philips_hue_favorites_for_wrong_component_type_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.put_json(route_url('nuimo_philips_hue_favorites', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='s1'), {
        "number": 1,
        "name": "station1 new name"
    }, status=404)
