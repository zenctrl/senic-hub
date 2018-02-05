import logging
import logging.config
import time
import os
import yaml
import configparser

from threading import Thread
from multiprocessing import Process, Queue

import click
import platform

if platform.system() == 'Linux':
    import pyinotify


from . import NuimoApp

import multiprocessing_logging
multiprocessing_logging.install_mp_handler()


if os.path.isfile('/etc/senic_hub.ini'):
    logging.config.fileConfig(
        '/etc/senic_hub.ini', disable_existing_loggers=False
    )


logger = logging.getLogger(__name__)


@click.command(help="configuration file for the Nuimo app")
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help="app configuration file")
@click.option('--verbose', '-v', count=True, help="Print info messages (-vv for debug messages)")
def main(config, verbose):
    # There are multiple 'config' variables throughout the runtime of app
    # each meaning a different thing. I can't rename it due to the click
    # dependency "--config", so the hacky refactoring
    senic_hub_ini = config
    del config

    log_format = '%(processName)s  %(threadName)s %(levelname)-5.5s [%(name)s:%(lineno)d] \t %(message)s'

    if verbose >= 2:
        logging.basicConfig(level=logging.DEBUG, format=log_format)
    elif verbose >= 1:
        logging.basicConfig(level=logging.INFO, format=log_format)
    else:
        logging.basicConfig(level=logging.WARNING, format=log_format)

    # TODO: remove too verbose logging messages like this
    logger.info("--- Start ----")

    # urllib3 logger is very verbose so we hush it down
    logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)
    logging.getLogger("soco").setLevel(logging.WARNING)

    config_parser = configparser.ConfigParser()
    config_parser.read(senic_hub_ini)

    # Here config_path references nuimo_app.cfg
    config_path = config_parser['app:senic_hub']['nuimo_app_config_path']
    ble_adapter_name = config_parser['app:senic_hub']['bluetooth_adapter_name']

    nuimo_apps = {}
    queues = {}
    processes = {}

    # nuimo_app can't progress unless /data/senic-hub/nuimo_app.cfg present.
    # A poor man's waiting loop
    # This implies
    # autostart=true
    # autorestart=true
    # in supervisor conf for nuimo_app.conf
    tmp_counter = 0
    logger.info("Waiting for %s to be created" % config_path)
    while not os.path.exists(config_path):
        if tmp_counter == 10:
            logger.info("Waiting for %s to be created" % config_path)
            tmp_counter = -1
        time.sleep(1)
        tmp_counter += 1

    # nuimo_app can't progress unless a network connection is present
    adapter_name = "wlan0"
    logger.info("Checking there is an ip for %s..." % adapter_name)
    while True:
        try:
            ip = get_ip_address(adapter_name)
        except IOError:
            logger.info("No ip detected for %s. Waiting..." % adapter_name)
            time.sleep(5)
            continue
        break

    logger.info("Detected %s for %s..." % (ip, adapter_name))

    update_from_config_file(config_path, queues, nuimo_apps, processes, ble_adapter_name)

    logger.info("Watching %s for changes" % config_path)
    watch_config_thread = Thread(
        target=watch_config_changes,
        name="watch_config_thread",
        args=(config_path, queues, nuimo_apps, processes, ble_adapter_name),
        daemon=True)
    logger.debug("Started thread %s" % watch_config_thread.name)
    watch_config_thread.start()

    try:
        with open(config_path, 'r') as f:
            config = yaml.load(f)
        for mac_addr in config['nuimos']:
            components = config['nuimos'][mac_addr].get('components', [])
            app = NuimoApp(ble_adapter_name, mac_addr, components)
            ipc_queue = Queue()
            queues[mac_addr] = ipc_queue
            nuimo_apps[mac_addr] = components
            # [Alan] For each nuimo a separate process is spawned
            # This is required because this NuimoApp instance is executed
            # in its own process (because gatt-python doesn't handle multiple
            # devices in a single thread correctly) and it needs to be notified
            # of changes and when to quit

            processes[mac_addr] = Process(name="nuimo-%s" % mac_addr,
                                          target=app.start,
                                          args=(ipc_queue,),
                                          daemon=True)
            logger.debug("Starting nuimo BT control process %s"
                         % processes[mac_addr].name)
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


def update_from_config_file(config_path, queues, nuimo_apps, processes, ble_adapter_name):
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


def watch_config_changes(config_path, queues, nuimo_apps, processes, ble_adapter_name):

    class ModificationHandler(pyinotify.ProcessEvent):

        def process_IN_CLOSE_WRITE(self, event):
            if hasattr(event, 'pathname') and event.pathname == config_path:
                logger.info("Config file was changed, reloading it...")
                update_from_config_file(config_path, queues, nuimo_apps, processes, ble_adapter_name)

    handler = ModificationHandler()
    watch_manager = pyinotify.WatchManager()
    notifier = pyinotify.Notifier(watch_manager, handler)
    # IN_CLOSE_WRITE is fired when the file was closed after modification
    # in opposite to IN_MODIFY which is called for each partial write
    watch_manager.add_watch(config_path, pyinotify.IN_CLOSE_WRITE)
    logger.info("Listening to changes of: %s", config_path)
    notifier.loop()
    logger.info("Stopped listening to changes of: %s", config_path)


import socket
import fcntl
import struct


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', bytes(ifname[:15], 'utf-8'))
    )[20:24])


if __name__ == "__main__":
    main()
