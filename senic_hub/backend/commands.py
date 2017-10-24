import json
import logging

import yaml

from . import supervisor
from .views.nuimo_components import create_component


COMPONENT_FOR_TYPE = {
    'sonos': 'sonos',
    'soundtouch': 'media_player',
    'philips_hue': 'philips_hue',
}

logger = logging.getLogger(__name__)

import os.path


def create_configuration_files_and_restart_apps(settings):
    # generate homeassistant config & restart supervisor app
    try:
        with open(settings['devices_path'], 'r') as f:
            devices = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        logger.error(e)

    homeassistant_config_path = settings['homeassistant_config_path']
    with open(homeassistant_config_path, 'w') as f:
        yaml.dump(generate_hass_configuration(devices), f, default_flow_style=False)

    # TODO: Restart home assistant again once it's part of SenicOS
    # supervisor.restart_program('homeassistant')

    # generate nuimo app config & restart supervisor app
    nuimo_mac_address_file_path = settings['nuimo_mac_address_filepath']
    with open(nuimo_mac_address_file_path, 'r') as f:
        nuimo_mac_address = f.readline().strip()

    nuimo_app_config_file_path = settings['nuimo_app_config_path']

    if os.path.isfile(nuimo_app_config_file_path) is False:
        with open(nuimo_app_config_file_path, 'w') as f:
            logger.info("file is empty")
            config = generate_nuimo_app_configuration(nuimo_mac_address, devices)
            yaml.dump(config, f, default_flow_style=False)
    else:
        with open(nuimo_app_config_file_path, 'r+') as f:
            config = yaml.load(f) or None
            logger.info("file has another configured nuimo")

            components = [create_component(d) for d in devices if d["authenticated"]]
            config['nuimos'][nuimo_mac_address] = {
                'name': 'My Nuimo ' + str(len(config['nuimos']) + 1),
                'components': components,
            }
            f.seek(0)  # We want to overwrite the config file with the new configuration
            f.truncate()
            yaml.dump(config, f, default_flow_style=False)

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


def generate_nuimo_app_configuration(nuimo_mac_address, devices):
    components = [create_component(d) for d in devices if d["authenticated"]]

    config = {'nuimos': {}}
    config['nuimos'][nuimo_mac_address] = {
        'name': 'My Nuimo',
        'components': components,
    }
    return config
