import logging
import os
import sys
import yaml

from importlib import import_module
from os.path import abspath
from threading import Thread

import click
import pyinotify

from pyramid.paster import get_app, setup_logging

from . import NuimoApp


logger = logging.getLogger(__name__)


@click.command(help="configuration file for the Nuimo app")
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
    # TODO: create multiple NuimoApps for all Nuimos mentioned in the config file

    nuimo_apps = {}
    nuimo_apps[nuimo_controller_mac_address] = nuimo_app
    watch_config_thread = Thread(
        target=watch_config_changes, args=(config_file_path, nuimo_apps), daemon=True)
    watch_config_thread.start()

    try:
        nuimo_app.start()
    except KeyboardInterrupt:
        logger.debug("Stopping...")
        nuimo_app.stop()


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


def watch_config_changes(config_path, nuimo_apps):

    class ModificationHandler(pyinotify.ProcessEvent):

        def process_IN_CLOSE_WRITE(self, event):
            if hasattr(event, 'pathname') and event.pathname == config_path:
                logger.info("Config file was changed, reloading it...")
                reload_config_file(config_path, nuimo_apps)

    handler = ModificationHandler()
    watch_manager = pyinotify.WatchManager()
    notifier = pyinotify.Notifier(watch_manager, handler)
    # IN_CLOSE_WRITE is fired when the file was closed after modification
    # in opposite to IN_MODIFY which is called for each partial write
    watch_manager.add_watch(config_path, pyinotify.IN_CLOSE_WRITE)
    logger.info("Listening to changes of: %s", config_path)
    notifier.loop()


def reload_config_file(config_path, nuimo_apps):
    with open(config_path, 'r') as f:
        config = yaml.load(f)

    nuimos = config['nuimos']

    for mac_addr in nuimo_apps.keys():
        if mac_addr not in nuimos:
            logger.info("A Nuimo was removed from the config file: %s", mac_addr)
            # TODO: stop NuimoApp for deleted Nuimo here

    for mac_addr in nuimos.keys():
        if mac_addr in nuimo_apps:
            logger.info("Updating app for Nuimo with address: %s", mac_addr)
            components = nuimos[mac_addr]['components']
            component_instances = get_component_instances(components)
            nuimo_apps[mac_addr].set_components(component_instances)
        else:
            logger.info("A Nuimo was added to the config file: %s", mac_addr)
            # TODO: create new NuimoApp for added Nuimo here


if __name__ == "__main__":
    main()
