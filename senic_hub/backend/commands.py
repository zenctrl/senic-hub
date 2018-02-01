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
    try:
        with open(settings['devices_path'], 'r') as f:
            devices = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        logger.error(e)

    nuimo_mac_address_file_path = settings['nuimo_mac_address_filepath']
    with open(nuimo_mac_address_file_path, 'r') as f:
        nuimo_mac_address = f.readline().strip()

    nuimo_app_config_file_path = settings['nuimo_app_config_path']
    logger.debug("Nuimo app config path: %s" % nuimo_app_config_file_path)

    if os.path.isfile(nuimo_app_config_file_path) is False:
        with open(nuimo_app_config_file_path, 'w') as f:
            logger.debug("%s not present, creating..." % nuimo_app_config_file_path)
            logger.info("No Nuimos registered do far. Creating init file for Nuimos.")

            config = generate_nuimo_app_configuration(nuimo_mac_address, devices)
            logger.debug("Writing %s into %s" % (config, nuimo_app_config_file_path))
            yaml.dump(config, f, default_flow_style=False)
    else:
        with open(nuimo_app_config_file_path, 'r+') as f:
            config = yaml.load(f) or None
            logger.debug("%s present" % nuimo_app_config_file_path)
            logger.info("A nuimo has beed registered on this Hub")

            components = [create_component(d) for d in devices if d["authenticated"]]
            config['nuimos'][nuimo_mac_address] = {
                'name': 'My Nuimo ' + str(len(config['nuimos']) + 1),
                'components': components,
            }
            f.seek(0)  # We want to overwrite the config file with the new configuration
            f.truncate()
            logger.debug("Writing %s into %s" % (config, nuimo_app_config_file_path))
            yaml.dump(config, f, default_flow_style=False)



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
