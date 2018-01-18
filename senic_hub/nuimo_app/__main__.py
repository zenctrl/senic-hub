import logging
import time
import os
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
    log_format = '%(threadName)s %(asctime)s %(levelname)-5.5s [%(name)s] %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_format)

    # TODO: remove too verbose logging messages like this
    logger.info("--- Start ----")

    # urllib3 logger is very verbose so we hush it down
    logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)

    app = get_app(abspath(config), name='senic_hub')
    logger.debug("app = %s" % app)

    config_path = app.registry.settings['nuimo_app_config_path']
    logger.debug("config_path = %s" % config_path)

    ha_api_url = app.registry.settings['homeassistant_api_url']
    ble_adapter_name = app.registry.settings['bluetooth_adapter_name']
    logger.debug("ble_adapter_name = %s" % ble_adapter_name)

    nuimo_apps = {}
    queues = {}
    processes = {}
    # creating initial nuimo apps:
    update_from_config_file(config_path, queues, nuimo_apps, processes, ha_api_url, ble_adapter_name)

    if platform.system() == 'Linux':
        watch_config_thread = Thread(
            target=watch_config_changes,
            name="watch_config_thread",
            args=(config_path, queues, nuimo_apps, processes, ha_api_url, ble_adapter_name),
            daemon=True)
        watch_config_thread.start()
        logger.info("Started watch_config_thread")
        logger.debug("config_path = %s" % config_path)

    elif not queues:
        logger.error("No Nuimos configured and can't watch config for changes!")

    try:
        with open(config_path, 'r') as f:
            config = yaml.load(f)
        for mac_addr in config['nuimos']:
            components = config['nuimos'][mac_addr].get('components', [])
            app = NuimoApp(ha_api_url, ble_adapter_name, mac_addr, components)
            ipc_queue = Queue()
            queues[mac_addr] = ipc_queue
            nuimo_apps[mac_addr] = components
            processes[mac_addr] = Process(target=app.start, args=(ipc_queue,))
            processes[mac_addr].start()

    except FileNotFoundError as e:
        logger.error(e)

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received SIGINT, stopping all nuimo apps...")
            break

    for mac_addr in queues.keys():
        queues[mac_addr].put({'method': 'stop'})
        processes[mac_addr].join()

    os.system('systemctl restart bluetooth')

    logger.info("Stopped all nuimo apps")


def update_from_config_file(config_path, queues, nuimo_apps, processes, ha_api_url, ble_adapter_name):
    try:
        with open(config_path, 'r') as f:
            config = yaml.load(f)

        logger.debug("Loading config file %s = %s" % (config_path, config))
        updated_nuimos = config['nuimos']

        # TODO: remove nuimos without restart nuimo_app code

        for mac_addr in updated_nuimos.keys():
            components = updated_nuimos[mac_addr].get('components', [])
            if mac_addr in nuimo_apps and components != nuimo_apps[mac_addr]:
                logger.debug("nuimo_apps= %s", nuimo_apps[mac_addr])
                logger.info("Updating app for Nuimo with address: %s", mac_addr)
                queues[mac_addr].put({'method': 'set_components', 'components': components})
                nuimo_apps[mac_addr] = components
            # TODO: add nuimos without restart nuimo_app code

    except FileNotFoundError as e:
        logger.error(e)


def watch_config_changes(config_path, queues, nuimo_apps, processes, ha_api_url, ble_adapter_name):

    class ModificationHandler(pyinotify.ProcessEvent):

        def process_IN_CLOSE_WRITE(self, event):
            if hasattr(event, 'pathname') and event.pathname == config_path:
                logger.info("Config file was changed, reloading it...")
                update_from_config_file(config_path, queues, nuimo_apps, processes, ha_api_url, ble_adapter_name)

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
