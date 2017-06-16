import configparser
import logging
import sys

from importlib import import_module
from os.path import abspath

import click

from pyramid.paster import get_app, setup_logging

from . import NuimoApp


logger = logging.getLogger(__name__)


@click.command(help="confifguration file for the Nuimo app")
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help="app configuration file")
def main(config):
    app = get_app(abspath(config), name='senic_hub_backend')
    setup_logging(config)

    # urllib3 logger is very verbose so we hush it down
    logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)

    config, component_config = read_config(app.registry.settings['nuimo_app_config_path'])
    logger.info("Using configuration from: %s", app.registry.settings['nuimo_app_config_path'])

    nuimo_controller_mac_address_file_path = app.registry.settings['nuimo_mac_address_filepath']
    try:
        with open(nuimo_controller_mac_address_file_path, 'r') as f:
            nuimo_controller_mac_address = f.readline().strip()
    except IOError:
        nuimo_controller_mac_address = None

    if not nuimo_controller_mac_address:
        logger.error("Nuimo controller MAC address not configured")
        sys.exit(1)

    ha_api_url = app.registry.settings['homeassistant_api_url']
    ble_adapter_name = app.registry.settings['bluetooth_adapter_name']
    component_instances = get_component_instances(component_config)
    nuimo_app = NuimoApp(ha_api_url, ble_adapter_name, nuimo_controller_mac_address, component_instances)

    try:
        nuimo_app.start()
    except KeyboardInterrupt:
        logger.debug("Stopping...")
        nuimo_app.stop()


def read_config(config_file_path):
    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config["DEFAULT"], config


def get_component_instances(component_config):
    """
    Import component modules configured in the Nuimo app configuration
    and return instances of the contained component classes.
    """
    instances = []

    module_name_format = __name__.rsplit('.', 1)[0] + '.components.{}'

    for component_id in component_config.sections():
        config = component_config[component_id]
        module_name = module_name_format.format(config.pop('type'))
        logger.info("Importing module %s", module_name)
        component_module = import_module(module_name)
        instances.append(component_module.Component(component_id, config))

    return instances


if __name__ == "__main__":
    main()
