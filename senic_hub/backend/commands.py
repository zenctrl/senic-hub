import click
import json
import logging
import os
import signal
import sys
import time

from os.path import abspath
from subprocess import PIPE, TimeoutExpired
from datetime import datetime, timedelta
from .subprocess_run import run

import wifi
from pyramid.paster import get_app, setup_logging

import configparser

import yaml

from . import supervisor

from .device_discovery import discover_and_update_devices


DEFAULT_IFACE = 'wlan0'
IFACES_AVAILABLE = '/etc/network/interfaces.available/{}'
IFACES_D = '/etc/network/interfaces.d/{}'
WPA_SUPPLICANT_FS = '/etc/wpa_supplicant/wpa_supplicant.conf'
WPA_SUPPLICANT_CONF = '''ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
network={{
    ssid="{ssid}"
    psk="{password}"
}}
'''
DEFAULT_SCAN_INTERVAL_SECONDS = 1 * 60  # 1 minute


logger = logging.getLogger(__name__)


def get_networks(devices=[DEFAULT_IFACE]):
    networks = dict()
    for device in devices:
        networks.update({c.ssid: dict(device=device, cell=c) for c in wifi.Cell.all(device)})
    return networks


@click.command(help='scan the wifi interfaces for networks (requires root privileges)')
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help='app configuration file')
@click.option('--forever/--no-forever', default=False, help='scan forever (until interupted')
@click.option('--waitsec', default=20, help='How many seconds to wait inbetween scans (only when forever')
@click.argument('devices', nargs=-1)
def scan_wifi(config, devices, forever=False, waitsec=20):
    if devices == ():
        devices = [DEFAULT_IFACE]
    while True:
        click.echo("Scanning for wifi networks")
        networks = get_networks(devices=devices)
        json_networks = {n['cell'].ssid: dict(device=n['device']) for n in networks.values()}
        app = get_app(abspath(config))
        with open(app.registry.settings['wifi_networks_path'], 'w') as wifi_file:
            json.dump(json_networks, wifi_file)
        if not forever:
            exit(0)
        time.sleep(waitsec)


def activate_adhoc(device=DEFAULT_IFACE):
    run(['ifdown', device])
    try:
        os.remove(IFACES_D.format(device))
    except FileNotFoundError:
        pass
    # new symlink
    os.symlink(
        IFACES_AVAILABLE.format('interfaces_setup_wifi'),
        IFACES_D.format(device)
    )
    run(['ifup', device])


@click.command(help='Activate the wifi-onboarding setup')
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help='app configuration file')
@click.argument('device', default=DEFAULT_IFACE)
def enter_wifi_setup(config, device=DEFAULT_IFACE):
    app = get_app(abspath(config))
    WIFI_SETUP_FLAG_PATH = app.registry.settings['wifi_setup_flag_path']
    if not os.path.exists(WIFI_SETUP_FLAG_PATH):
        click.echo("Not entering wifi setup mode. %s not found" % WIFI_SETUP_FLAG_PATH)
        exit(0)
    activate_adhoc(device)
    run(['/usr/bin/supervisorctl', 'start', 'scan_wifi'])
    click.echo("Entering wifi setup mode")
    retries = 3
    success = False
    while retries > 0:
        activate_adhoc(device)
        run(['/usr/bin/supervisorctl', 'start', 'dhcpd'])
        dhcpd_status = run(
            ['/usr/bin/supervisorctl', 'status', 'dhcpd'],
            stdout=PIPE)
        retries -= 1
        success = 'RUNNING' in dhcpd_status.stdout.decode()
        if success:
            run(['/bin/systemctl', 'restart', 'avahi-daemon'])
            # signal that we no longer have joined a wifi
            JOINED_WIFI = app.registry.settings['joined_wifi_path']
            if os.path.exists(JOINED_WIFI):
                os.remove(JOINED_WIFI)
            exit("Successfully entered wifi setup mode")
        click.echo("Retrying...")
    click.echo("Unable to enter wifi setup mode. Check supervisord log for details")


@click.command(help='join a given wifi network (requires root privileges)')
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help='app configuration file')
@click.argument('ssid')
@click.argument('password')
@click.argument('device', default=DEFAULT_IFACE)
def join_wifi(config, ssid, password, device=DEFAULT_IFACE):
    app = get_app(abspath(config))
    # signal, that we've started to join:
    with open(app.registry.settings['joined_wifi_path'], 'w') as joined_wifi:
        joined_wifi.write(json.dumps(dict(ssid=ssid, status='connecting')))
    run(['/usr/bin/supervisorctl', 'stop', 'scan_wifi'])
    run(['/usr/bin/supervisorctl', 'stop', 'dhcpd'])
    run(['ifdown', device])
    try:
        os.remove(IFACES_D.format(device))
    except FileNotFoundError:
        pass
    # new symlink
    os.symlink(
        IFACES_AVAILABLE.format('interfaces_dhcp_wifi'),
        IFACES_D.format(device)
    )
    with open(WPA_SUPPLICANT_FS, 'w') as wpaconf:
        wpaconf.write(WPA_SUPPLICANT_CONF.format(**locals()))
    try:
        run(['ifup', device], timeout=30)
        # check, if we were successful:
        status = run(['wpa_cli', 'status'], stdout=PIPE)
        success = 'wpa_state=COMPLETED' in status.stdout.decode()
    except TimeoutExpired:
        success = False

    WIFI_SETUP_FLAG_PATH = app.registry.settings['wifi_setup_flag_path']

    if success:
        # clean up after ourselves
        with open(app.registry.settings['joined_wifi_path'], 'w') as joined_wifi:
            joined_wifi.write(json.dumps(dict(ssid=ssid, status='connected')))
        if os.path.exists(WIFI_SETUP_FLAG_PATH):
            os.remove(WIFI_SETUP_FLAG_PATH)
        run(['/bin/systemctl', 'restart', 'avahi-daemon'])
        click.echo("Success!")
        exit(0)
    else:
        click.echo("Could not join %s." % ssid)
        # signal the setup mode is active because of
        # failed attempt (as opposed to not having tried
        # yet).
        with open(WIFI_SETUP_FLAG_PATH, 'w') as flag:
            flag.write('FAILED')
        exit(1)


@click.command(help='create configuration files for nuimo app & hass and restart them')
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help='app configuration file')
def create_configuration_files_and_restart_apps(config):
    app = get_app(abspath(config))
    create_configuration_files_and_restart_apps_(app.registry.settings)


def create_configuration_files_and_restart_apps_(settings):
    # generate homeassistant config & restart supervisor app
    with open(settings['devices_path'], 'r') as f:
        devices = json.load(f)

    hass_config_file_path = settings['hass_config_path']
    with open(hass_config_file_path, 'w') as f:
        yaml.dump(generate_hass_configuration(devices), f, default_flow_style=False)

    supervisor.restart_program('nuimo_hass')

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

    bridge_ips = [x['ip'] for x in devices if x['type'] == 'philips_hue']
    if bridge_ips:
        hass_configuration['light'] = [{'platform': 'hue', 'host': x} for x in bridge_ips]

    return hass_configuration


def generate_nuimo_configuration(devices, nuimo_controller_mac_address, bluetooth_adapter_name):
    config = configparser.ConfigParser()
    config['DEFAULT'] = {
        'ha_api_url': 'localhost:8123',
        'logging_level': 'DEBUG',
        'controller_mac_address': nuimo_controller_mac_address,
        'bluetooth_adapter_name': bluetooth_adapter_name,
    }
    for index, device in enumerate(devices):
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
def discover_devices(config):
    app = get_app(abspath(config))
    setup_logging(config)

    devices_path = app.registry.settings['devices_path']
    scan_interval_seconds = app.registry.settings.get(
        'scan_interval_seconds', DEFAULT_SCAN_INTERVAL_SECONDS)

    # install Ctrl+C handler
    signal.signal(signal.SIGINT, sigint_handler)

    if os.path.exists(devices_path):
        with open(devices_path, 'r') as f:
            devices = json.load(f)
    else:
        devices = []

    while True:
        now = datetime.utcnow()
        devices = discover_and_update_devices(devices, now)
        with open(devices_path, 'w') as f:
            json.dump(devices, f)

        next_scan = now + timedelta(seconds=scan_interval_seconds)
        logging.info("Next device discovery run scheduled for %s", next_scan)
        time.sleep(scan_interval_seconds)
