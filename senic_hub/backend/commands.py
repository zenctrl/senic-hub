import click
import json
import logging
import os
import signal
import sys
import time

from os.path import abspath, exists
from datetime import datetime, timedelta
from pyramid.paster import get_app, setup_logging
from tempfile import mkstemp

import configparser

import yaml

from . import supervisor

from .device_discovery import PhilipsHueBridgeApiClient, discover_devices, read_json


DEFAULT_SCAN_INTERVAL_SECONDS = 1 * 60  # 1 minute

logger = logging.getLogger(__name__)


@click.command(help='create configuration files for nuimo app & hass and restart them')
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help='app configuration file')
def create_configuration_files_and_restart_apps(config):
    app = get_app(abspath(config))
    create_configuration_files_and_restart_apps_(app.registry.settings)


def create_configuration_files_and_restart_apps_(settings):
    # generate homeassistant config & restart supervisor app
    with open(settings['devices_path'], 'r') as f:
        devices = json.load(f)

    homeassistant_data_path = settings['homeassistant_data_path']
    hass_config_file_path = os.path.join(homeassistant_data_path, 'configuration.yaml')
    with open(hass_config_file_path, 'w') as f:
        yaml.dump(generate_hass_configuration(devices), f, default_flow_style=False)

    supervisor.restart_program('homeassistant')

    # generate nuimo app config & restart supervisor app
    nuimo_controller_mac_address_file_path = settings['nuimo_mac_address_filepath']
    with open(nuimo_controller_mac_address_file_path, 'r') as f:
        nuimo_controller_mac_address = f.readline().strip()

    nuimo_app_config_file_path = settings['nuimo_app_config_path']
    bluetooth_adapter_name = settings['bluetooth_adapter_name']
    with open(nuimo_app_config_file_path, 'w') as f:
        config = generate_nuimo_configuration(devices, nuimo_controller_mac_address, bluetooth_adapter_name)
        config.write(f)

    supervisor.restart_program('nuimo_app')


def generate_hass_configuration(devices):
    hass_configuration = {
        'api': '',
        'websocket_api': '',
    }

    sonos_speakers = [x['ip'] for x in devices if x['type'] == 'sonos']
    if sonos_speakers:
        hass_configuration['media_player'] = [{
            'platform': 'sonos',
            'hosts': sonos_speakers,
        }]

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


def generate_nuimo_configuration(devices, nuimo_controller_mac_address, bluetooth_adapter_name):
    config = configparser.ConfigParser()
    config['DEFAULT'] = {
        'ha_api_url': 'localhost:8123',
        'logging_level': 'DEBUG',
        'controller_mac_address': nuimo_controller_mac_address,
        'bluetooth_adapter_name': bluetooth_adapter_name,
    }
    authenticated_devices = [d for d in devices if d["authenticated"]]
    for index, device in enumerate(authenticated_devices):
        section_name = '{}-{}'.format(device['type'], index)
        component = {
            'philips_hue': 'PhilipsHue',
            'sonos': 'Sonos',
        }[device['type']]

        config[section_name] = {
            'name': section_name,
            'component': component,
            'entity_id': device["ha_entity_id"],
        }
    return config


def sigint_handler(*args):
    logger.info('Stopping...')
    sys.exit(0)


@click.command(help='scan for devices in local network and store their description in a file')
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help='app configuration file')
def device_discovery(config):
    app = get_app(abspath(config))
    setup_logging(config)

    devices_path = app.registry.settings['devices_path']
    scan_interval_seconds = int(app.registry.settings.get(
        'device_scan_interval_seconds', DEFAULT_SCAN_INTERVAL_SECONDS))

    # install Ctrl+C handler
    signal.signal(signal.SIGINT, sigint_handler)

    if exists(devices_path):
        with open(devices_path, 'r') as f:
            devices = json.load(f)
    else:
        devices = []

    while True:
        now = datetime.utcnow()
        devices = discover_devices(devices, now)

        add_authentication_status(devices, app.registry.settings)
        add_homeassistant_entity_ids(devices)

        fd, filename = mkstemp(dir=app.registry.settings['homeassistant_data_path'])
        with open(fd, "w") as f:
            json.dump(devices, f)
        os.rename(filename, devices_path)

        next_scan = now + timedelta(seconds=scan_interval_seconds)
        logging.info("Next device discovery run scheduled for %s", next_scan)
        time.sleep(scan_interval_seconds)


def add_authentication_status(devices, settings):
    for device in devices:
        if not device["authenticationRequired"]:
            device["authenticated"] = True
            continue

        if device["type"] != "philips_hue":
            continue

        philips_hue_bridge_config_path = os.path.join(
            settings["homeassistant_data_path"],
            "{}.conf".format(device["id"]),
        )
        config = read_json(philips_hue_bridge_config_path, {})
        username = config.get(device["ip"], {}).get("username")

        api = PhilipsHueBridgeApiClient(device["ip"], username)
        device["authenticated"] = api.is_authenticated()


def add_homeassistant_entity_ids(devices):
    for device in devices:
        if device["type"] == "philips_hue":
            # TODO group has to be created manually for now
            device["ha_entity_id"] = "light.senic_hub_demo"
        else:
            room_name = device["extra"]["roomName"]
            device["ha_entity_id"] = "media_player.{}".format(room_name.replace(" ", "_").lower())
