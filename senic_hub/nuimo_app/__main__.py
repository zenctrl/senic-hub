import logging
import time
import yaml

from os.path import abspath
from threading import Thread
from multiprocessing import Process, Queue

import click
import platform

if platform.system() == 'Linux':
    import pyinotify

from pyramid.paster import get_app

from . import NuimoApp


logger = logging.getLogger(__name__)


@click.command(help="configuration file for the Nuimo app")
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help="app configuration file")
def main(config):
    log_format = '%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_format)

    # TODO: remove too verbose logging messages like this
    logger.debug("--- Start ----")

    # urllib3 logger is very verbose so we hush it down
    logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)

    app = get_app(abspath(config), name='senic_hub')

    config_path = app.registry.settings['nuimo_app_config_path']

    ha_api_url = app.registry.settings['homeassistant_api_url']
    ble_adapter_name = app.registry.settings['bluetooth_adapter_name']

    nuimo_apps = {}
    # creating initial nuimo apps:
    update_from_config_file(config_path, nuimo_apps, ha_api_url, ble_adapter_name)

    if platform.system() == 'Linux':
        watch_config_thread = Thread(
            target=watch_config_changes,
            args=(config_path, nuimo_apps, ha_api_url, ble_adapter_name),
            daemon=True)
        watch_config_thread.start()
    elif not nuimo_apps:
        logger.error("No Nuimos configured and can't watch config for changes!")

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received SIGINT, stopping all nuimo apps...")
            break

    for nuimo_app_queue in nuimo_apps.values():
        nuimo_app_queue.put({'method': 'stop'})
    logger.debug("Stopped all nuimo apps")


def update_from_config_file(config_path, nuimo_apps, ha_api_url, ble_adapter_name):
    with open(config_path, 'r') as f:
        config = yaml.load(f)

    updated_nuimos = config['nuimos']

    for mac_addr in nuimo_apps.keys():
        if mac_addr not in updated_nuimos:
            logger.info("A Nuimo was removed from the config file: %s", mac_addr)
            nuimo_apps[mac_addr].put({'method': 'stop'})

    for mac_addr in updated_nuimos.keys():
        components = updated_nuimos[mac_addr].get('components', [])
        if mac_addr in nuimo_apps:
            logger.info("Updating app for Nuimo with address: %s", mac_addr)
            nuimo_apps[mac_addr].put({'method': 'set_components',
                                      'components': components})
        else:
            logger.info("A new Nuimo was found in the config file: %s", mac_addr)
            app = NuimoApp(ha_api_url, ble_adapter_name,
                     mac_addr, components)
            ipc_queue = Queue()
            nuimo_apps[mac_addr] = ipc_queue
            Process(target=app.start, args=(ipc_queue,)).start()


def watch_config_changes(config_path, nuimo_apps, ha_api_url, ble_adapter_name):

    class ModificationHandler(pyinotify.ProcessEvent):

        def process_IN_CLOSE_WRITE(self, event):
            if hasattr(event, 'pathname') and event.pathname == config_path:
                logger.info("Config file was changed, reloading it...")
                update_from_config_file(config_path, nuimo_apps, ha_api_url, ble_adapter_name)

    handler = ModificationHandler()
    watch_manager = pyinotify.WatchManager()
    notifier = pyinotify.Notifier(watch_manager, handler)
    # IN_CLOSE_WRITE is fired when the file was closed after modification
    # in opposite to IN_MODIFY which is called for each partial write
    watch_manager.add_watch(config_path, pyinotify.IN_CLOSE_WRITE)
    logger.info("Listening to changes of: %s", config_path)
    notifier.loop()
    logger.info("Stopped listening to changes of: %s", config_path)


if __name__ == "__main__":
    main()
