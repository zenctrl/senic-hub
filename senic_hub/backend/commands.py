import click
import json
import logging
import os
import signal
import sys
import time

from os.path import abspath
from datetime import datetime, timedelta
from pyramid.paster import get_app, setup_logging
from tempfile import mkstemp

import configparser

import yaml

from . import supervisor

from .device_discovery import PhilipsHueBridgeApiClient, discover_devices
from .views.nuimo_components import component_to_app_config_component, create_component


DEFAULT_SCAN_INTERVAL_SECONDS = 1 * 60  # 1 minute

COMPONENT_FOR_TYPE = {
    'sonos': 'sonos',
    'soundtouch': 'media_player',
    'philips_hue': 'philips_hue',
}

logger = logging.getLogger(__name__)


@click.command(help='create configuration files for nuimo app & hass and restart them')
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help='app configuration file')
def create_configuration_files_and_restart_apps(config):
    app = get_app(abspath(config), name='senic_hub')
    create_configuration_files_and_restart_apps_(app.registry.settings)


def create_configuration_files_and_restart_apps_(settings):
    # generate homeassistant config & restart supervisor app
    with open(settings['devices_path'], 'r') as f:
        devices = json.load(f)

    homeassistant_config_path = settings['homeassistant_config_path']
    with open(homeassistant_config_path, 'w') as f:
        yaml.dump(generate_hass_configuration(devices), f, default_flow_style=False)

    supervisor.restart_program('homeassistant')

    # generate nuimo app config & restart supervisor app
    nuimo_app_config_file_path = settings['nuimo_app_config_path']
    with open(nuimo_app_config_file_path, 'w') as f:
        config = generate_nuimo_app_configuration(devices)
        config.write(f)

    supervisor.restart_program('nuimo_app')


def generate_hass_configuration(devices):
    hass_configuration = {
        'api': '',
        'websocket_api': '',
    }

    media_players = []

    sonos_speakers = [d for d in devices if d['type'] == 'sonos']
    for speaker in sonos_speakers:
        media_players.append({
            'platform': 'sonos',
            'host': speaker['ip'],
        })

    soundtouch_speakers = [d for d in devices if d['type'] == 'soundtouch']
    for speaker in soundtouch_speakers:
        media_players.append({
            'platform': 'soundtouch',
            'host': speaker['ip'],
            'port': speaker['port'],
        })

    if media_players:
        hass_configuration['media_player'] = media_players

    phue_bridges = [d for d in devices if d['type'] == 'philips_hue' and d['authenticated']]
    if phue_bridges:
        hass_configuration['light'] = [phue_bridge_config(b) for b in phue_bridges]

    return hass_configuration


def phue_bridge_config(bridge):
    return {
        'platform': 'hue',
        'host': bridge['ip'],
        'filename': '{}.conf'.format(bridge['id']),
    }


def generate_nuimo_app_configuration(devices):
    config = configparser.ConfigParser()
    authenticated_devices = [d for d in devices if d["authenticated"]]
    for device in authenticated_devices:
        component = component_to_app_config_component(create_component(device))
        config[component['id']] = component

    return config


def sigint_handler(*args):
    logger.info('Stopping...')
    sys.exit(0)


@click.command(help='scan for devices in local network and store their description in a file')
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help='app configuration file')
def device_discovery(config):
    app = get_app(abspath(config), name='senic_hub')
    setup_logging(config)

    devices_path = app.registry.settings['devices_path']
    scan_interval_seconds = int(app.registry.settings.get(
        'device_scan_interval_seconds', DEFAULT_SCAN_INTERVAL_SECONDS))

    # install Ctrl+C handler
    signal.signal(signal.SIGINT, sigint_handler)

    while True:
        try:
            with open(devices_path, 'r') as f:
                devices = json.load(f)
        except OSError as e:
            logging.warning("Could not open devices file %s", devices_path)
            logging.warning(e, exc_info=True)
        except json.decoder.JSONDecodeError as e:
            logging.warning("Could not JSON-decode devices file %s", devices_path)
            logging.warning(e, exc_info=True)
        finally:
            devices = []

        now = datetime.utcnow()
        devices = discover_devices(devices, now)

        add_authentication_status(devices)
        add_device_details(devices)
        add_homeassistant_entity_ids(devices)

        fd, filename = mkstemp(dir=app.registry.settings['homeassistant_data_path'])
        with open(fd, "w") as f:
            json.dump(devices, f)
        os.rename(filename, devices_path)

        next_scan = now + timedelta(seconds=scan_interval_seconds)
        logging.info("Next device discovery run scheduled for %s", next_scan)
        time.sleep(scan_interval_seconds)


def add_authentication_status(devices):
    for device in devices:
        if not device["authenticationRequired"]:
            device["authenticated"] = True
            continue

        if device["type"] != "philips_hue":
            continue

        api = PhilipsHueBridgeApiClient(device["ip"], device['extra'].get('username'))
        device["authenticated"] = api.is_authenticated()


def add_device_details(devices):
    authenticated_bridges = [d for d in devices if d['type'] == 'philips_hue' and d['authenticated']]
    for bridge in authenticated_bridges:
        api = PhilipsHueBridgeApiClient(bridge["ip"], bridge['extra']['username'])
        bridge['extra']['lights'] = api.get_lights()


def add_homeassistant_entity_ids(devices):
    for device in devices:
        if device["type"] == "philips_hue":
            device["ha_entity_id"] = "light.senic_hub"
        elif device["type"] == "soundtouch":
            device["ha_entity_id"] = "media_player.bose_soundtouch"
        elif device["type"] == "sonos":
            room_name = device["extra"]["roomName"]
            device["ha_entity_id"] = "media_player.{}".format(room_name.replace(" ", "_").lower())
