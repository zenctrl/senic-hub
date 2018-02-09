import json
import logging

import yaml

from . import supervisor
from .views.nuimo_components import create_component


COMPONENT_FOR_TYPE = {
    'sonos': 'sonos',
    'philips_hue': 'philips_hue',
}


logger = logging.getLogger(__name__)

import os.path
import os
import time


def create_nuimo_app_cfg(settings):
    """
    Creates nuimo_app.cfg a hard dependency for nuimo_app

    When there is no wifi present, netwatch kills the nuimo_app.
    This methog responsible for the initial starting of the nuimo_app
    once the hub got wifi connection the first time.
    This happens during the hub onboarding.

    Once the hub has been onboarded, the nuimo_app is started
    by default by supervisor.
    """

    logger.info("Creating config files that map Nuimo to Sonos/Hue")

    while not os.path.exists(settings['devices_path']):
        logger.info("Waiting for Sonos or Hue to be detected")
        logger.debug("Can't continue until %s has been created" %
                     settings['devices_path'])
        time.sleep(5)

    try:
        with open(settings['devices_path'], 'r') as f:
            devices = json.load(f)
    except (json.decoder.JSONDecodeError) as e:
        logger.error("%s doesn't contain a readable json" % settings['devices_path'])
        logger.error(e)

    # generate nuimo app config & restart supervisor app
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
                'name': 'My NUIMO ' + str(len(config['nuimos']) + 1),
                'components': components,
            }
            f.seek(0)  # We want to overwrite the config file with the new configuration
            f.truncate()
            logger.debug("Writing %s into %s" % (config, nuimo_app_config_file_path))
            yaml.dump(config, f, default_flow_style=False)

    if supervisor.program_status('nuimo_app') != 'RUNNING':
        supervisor.start_program('nuimo_app')


def generate_nuimo_app_configuration(nuimo_mac_address, devices):
    components = [create_component(d) for d in devices if d["authenticated"]]

    config = {'nuimos': {}}
    config['nuimos'][nuimo_mac_address] = {
        'name': 'My NUIMO',
        'components': components,
    }
    return config
