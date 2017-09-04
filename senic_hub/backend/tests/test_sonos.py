from os import remove
from pytest import fixture, yield_fixture
from tempfile import NamedTemporaryFile

import yaml


@fixture
def nuimo_sonos_favourl(route_url):
    return route_url('nuimo_sonos_favorites', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='s1')


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


def test_get_nuimo_sonos_favorites_returns_nuimo_favorites(nuimo_sonos_favourl, browser, temporary_nuimo_app_config_file, settings):
    nuimo_favorites = browser.get(nuimo_sonos_favourl, status=200).json

    assert set(nuimo_favorites) == set({
        'station1': {
            'uri': "station1 uri",
            'meta': "station1 meta",
            'title': "station1 title",
        },
        'station2': {
            'uri': "station2 uri",
            'meta': "station2 meta",
            'title': "station2 title",
        }, 'station3': {
            'uri': "station3 uri",
            'meta': "station3 meta",
            'title': "station3 title",
        }
    })


def test_get_nuimo_favorites_for_invalid_component_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.get(route_url('nuimo_sonos_favorites', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='invalid-id'), status=404)


def test_get_nuimo_favorites_for_invalid_nuimo_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.get(route_url('nuimo_sonos_favorites', mac_address='de:ad:be:ef:00:00'.replace(':', '-'), component_id='s1'), status=404)


def test_get_nuimo_favorites_for_wrong_component_type_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.get(route_url('nuimo_sonos_favorites', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='ph2'), status=404)


def test_put_nuimo_sonos_favorites(nuimo_sonos_favourl, browser, temporary_nuimo_app_config_file, settings):
    browser.put_json(nuimo_sonos_favourl, {
        "number": 1,
        "item": {
            "meta": "station1 new meta",
            "title": "station1 new title",
            "uri": "station1 new uri"
        }
    }, status=200)

    with open(settings['nuimo_app_config_path'], 'r') as f:
        config = yaml.load(f)

    component = next(c for c in config['nuimos']['00:00:00:00:00:00']['components'] if c['id'] == 's1')
    assert set(component['station1']) == set({
        "meta": "station1 new meta",
        "title": "station1 new title",
        "uri": "station1 new uri"
    })


def test_put_nuimo_favorites_for_invalid_component_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.put_json(route_url('nuimo_sonos_favorites', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='invalid-id'), {
        "number": 1,
        "item": {
            "meta": "station1 new meta",
            "title": "station1 new title",
            "uri": "station1 new uri"
        }
    }, status=404)


def test_put_nuimo_favorites_for_invalid_nuimo_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.put_json(route_url('nuimo_sonos_favorites', mac_address='de:ad:be:ef:00:00'.replace(':', '-'), component_id='s1'), {
        "number": 1,
        "item": {
            "meta": "station1 new meta",
            "title": "station1 new title",
            "uri": "station1 new uri"
        }
    }, status=404)


def test_put_nuimo_favorites_for_wrong_component_type_returns_404(route_url, browser, temporary_nuimo_app_config_file, settings):
    browser.put_json(route_url('nuimo_sonos_favorites', mac_address='00:00:00:00:00:00'.replace(':', '-'), component_id='ph2'), {
        "number": 1,
        "item": {
            "meta": "station1 new meta",
            "title": "station1 new title",
            "uri": "station1 new uri"
        }
    }, status=404)
