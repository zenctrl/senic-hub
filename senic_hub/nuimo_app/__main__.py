import logging
import yaml
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
    setup_logging(config)

    # urllib3 logger is very verbose so we hush it down
    logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)

    app = get_app(abspath(config), name='senic_hub')

    config_file_path = app.registry.settings['nuimo_app_config_path']
    with open(config_file_path, 'r') as f:
        config = yaml.load(f)

    nuimos = config['nuimos']
    nuimo_controller_mac_address = list(nuimos.keys())[0]

    if not nuimo_controller_mac_address:
        logger.error("Nuimo controller MAC address not configured")
        sys.exit(1)

    ha_api_url = app.registry.settings['homeassistant_api_url']
    ble_adapter_name = app.registry.settings['bluetooth_adapter_name']
    components = nuimos[nuimo_controller_mac_address]['components']
    component_instances = get_component_instances(components)
    nuimo_app = NuimoApp(ha_api_url, ble_adapter_name, nuimo_controller_mac_address, component_instances)

    try:
        nuimo_app.start()
    except KeyboardInterrupt:
        logger.debug("Stopping...")
        nuimo_app.stop()


def read_config(config_file_path, mac_address):
    with open(config_file_path, 'r') as f:
        config = yaml.load(f)

    return config['nuimos'][mac_address]['components']


def get_component_instances(components):
    """
    Import component modules configured in the Nuimo app configuration
    and return instances of the contained component classes.
    """
    module_name_format = __name__.rsplit('.', 1)[0] + '.components.{}'

    instances = []
    for component in components:
        module_name = module_name_format.format(component['type'])
        logger.info("Importing module %s", module_name)
        component_module = import_module(module_name)
        instances.append(component_module.Component(component))

    return instances


if __name__ == "__main__":
    main()
