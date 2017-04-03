import click
import json
import logging
import os
import re
import signal
import sys
import time

from os.path import abspath
from subprocess import PIPE, TimeoutExpired
from datetime import datetime, timedelta
from tempfile import mkstemp

from .subprocess_run import run

import wifi
from pyramid.paster import get_app, setup_logging

import configparser

import yaml

from . import supervisor

from .device_discovery import PhilipsHueBridgeApiClient, discover_devices, read_json


IFACES_AVAILABLE = '/etc/network/interfaces.available/{}'
IFACES_D = '/etc/network/interfaces.d/{}'
WPA_SUPPLICANT_CONF_PATH = '/etc/wpa_supplicant/wpa_supplicant.conf'
WPA_SUPPLICANT_CONF_TEMPLATE = '''
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
network={{
    ssid="{ssid}"
    psk="{password}"
}}
'''
DEFAULT_SCAN_INTERVAL_SECONDS = 1 * 60  # 1 minute


logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help='app configuration file')
def wifi_setup(ctx, config):
    ctx.obj = get_app(abspath(config)).registry.settings


@wifi_setup.command(name='status', help="query wifi connection status")
@click.pass_context
def wifi_setup_status(ctx):
    wlan_infra = ctx.obj['wlan_infra']
    try:
        wpa_status = run(['wpa_cli', '-i', wlan_infra, 'status'], stdout=PIPE, timeout=5).stdout.decode()
    except TimeoutExpired:
        wpa_status = ""
    ssid_match = re.search("^ssid=(.*)$", wpa_status, flags=re.MULTILINE)
    ssid = ssid_match.group(1) if ssid_match else None
    ip_address_match = re.search("^ip_address=(.*)$", wpa_status, flags=re.MULTILINE)
    ip_address = ip_address_match.group(1) if ip_address_match else None
    connected = 'wpa_state=COMPLETED' in wpa_status
    if ssid and connected:
        status = 'connected' if ip_address else 'connecting'
    else:
        status = 'unavailable'
    click.echo("infra_ssid=%s" % (ssid or ""))
    click.echo("infra_status=%s" % status)


@wifi_setup.command(name='start', help="start the wifi setup by bringing up setup ad-hoc network")
@click.pass_context
def wifi_setup_start(ctx):
    WIFI_SETUP_FLAG_PATH = ctx.obj['wifi_setup_flag_path']
    if not os.path.exists(WIFI_SETUP_FLAG_PATH):
        click.echo("Not entering wifi setup mode. %s not found" % WIFI_SETUP_FLAG_PATH)
        exit(0)
    click.echo("Entering wifi setup mode")
    wlan_adhoc = ctx.obj['wlan_adhoc']
    wlan_infra = ctx.obj['wlan_infra']
    click.echo("Creating ad-hoc network with interface '%s'" % wlan_adhoc)
    activate_adhoc(wlan_adhoc)
    click.echo("Resetting interface '%s'" % wlan_infra)
    activate_infra(wlan_infra, ssid=None, password=None)
    click.echo("Start scanning nearby wifi networks")
    run(['/usr/bin/supervisorctl', 'start', 'scan_wifi'])
    click.echo("Restarting avahi daemon")
    run(['/bin/systemctl', 'restart', 'avahi-daemon'])
    click.echo("Wifi setup mode successfully entered")


def activate_adhoc(device):
    run(['ifup', device])


def activate_infra(device, ssid, password, timeout=None):
    """Throws `subprocess.TimeoutExpired` if `ifup` takes longer than `timeout`"""
    run(['ifdown', device])
    # TODO: Support password-less networks, `key_mgmt=NONE` must be added to `network` section
    with open(WPA_SUPPLICANT_CONF_PATH, 'w') as wpa_conf:
        if ssid and password:
            wpa_conf.write(WPA_SUPPLICANT_CONF_TEMPLATE.format(**locals()))
        else:
            wpa_conf.write('\n')
    run(['ifup', device], timeout=timeout)

@wifi_setup.command(name='join', help="join a given wifi network (requires root privileges)")
@click.pass_context
@click.argument('ssid')
@click.argument('password')
def wifi_setup_join(ctx, ssid, password):
    device = ctx.obj['wlan_infra']
    # Stop wifi scanner and DHCP daemon only if same wlan device is used for adhoc and infrastructure network
    if device == ctx.obj['wlan_adhoc']:
        click.echo("Stopping wifi scanner and bringing down ad-hoc network")
        run(['/usr/bin/supervisorctl', 'stop', 'scan_wifi'])
        run(['/usr/bin/supervisorctl', 'stop', 'dhcpd'])
    click.echo("Configuring '%s' for infrastructure mode" % device)
    try:
        activate_infra(device, ssid, password, timeout=30)
        # TODO: Better run `wifi_setup_status` to check status
        # TODO: Continue polling connection state as long as it's `connecting`
        status = run(['wpa_cli', '-i', device, 'status'], stdout=PIPE)
        success = 'wpa_state=COMPLETED' in status.stdout.decode()
    except TimeoutExpired:
        success = False

    if success:
        try:
            os.remove(ctx.obj['wifi_setup_flag_path'])
        except FileNotFoundError:
            pass
        run(['/bin/systemctl', 'restart', 'avahi-daemon'])
        click.echo("Joining wifi network '%s' succeeded" % ssid)
        exit(0)
    else:
        click.echo("Failed to join network '%s'" % ssid)
        exit(1)


@click.command(help='scan the wifi interfaces for networks (requires root privileges)')
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help='app configuration file')
@click.option('--forever/--no-forever', default=False, help='scan forever (until interupted')
@click.option('--waitsec', default=20, help='How many seconds to wait inbetween scans (only when forever')
def scan_wifi(config, forever=False, waitsec=20):
    app = get_app(abspath(config))
    device = app.registry.settings['wlan_infra']
    while True:
        click.echo("Scanning for wifi networks")
        try:
            networks = [c.ssid for c in wifi.Cell.all(device) if c.ssid]
        except wifi.exceptions.InterfaceError as e:
            click.echo("Scanning wifi networks failed: %s" % e)
            networks = []
        with open(app.registry.settings['wifi_networks_path'], 'w') as wifi_file:
            json.dump({'ssids': networks}, wifi_file, indent=2)
            wifi_file.write('\n')
        if not forever:
            exit(0)
        time.sleep(waitsec)


@click.command(help='create configuration files for nuimo app & hass and restart them')
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help='app configuration file')
def create_configuration_files_and_restart_apps(config):
    app = get_app(abspath(config))
    create_configuration_files_and_restart_apps_(app.registry.settings)


def create_configuration_files_and_restart_apps_(settings):
    # generate homeassistant config & restart supervisor app
    with open(settings['devices_path'], 'r') as f:
        devices = json.load(f)

    homeassistant_data_path = settings['homeassistant_data_path']
    hass_config_file_path = os.path.join(homeassistant_data_path, 'configuration.yaml')
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


def generate_nuimo_configuration(devices, nuimo_controller_mac_address, bluetooth_adapter_name):
    config = configparser.ConfigParser()
    config['DEFAULT'] = {
        'ha_api_url': 'localhost:8123',
        'logging_level': 'DEBUG',
        'controller_mac_address': nuimo_controller_mac_address,
        'bluetooth_adapter_name': bluetooth_adapter_name,
    }
    authenticated_devices = [d for d in devices if d["authenticated"]]
    for index, device in enumerate(authenticated_devices):
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
def device_discovery(config):
    app = get_app(abspath(config))
    setup_logging(config)

    devices_path = app.registry.settings['devices_path']
    scan_interval_seconds = int(app.registry.settings.get(
        'device_scan_interval_seconds', DEFAULT_SCAN_INTERVAL_SECONDS))

    # install Ctrl+C handler
    signal.signal(signal.SIGINT, sigint_handler)

    if os.path.exists(devices_path):
        with open(devices_path, 'r') as f:
            devices = json.load(f)
    else:
        devices = []

    while True:
        now = datetime.utcnow()
        devices = discover_devices(devices, now)

        add_authentication_status(devices, app.registry.settings)
        add_homeassistant_entity_ids(devices)

        fd, filename = mkstemp(dir=app.registry.settings['homeassistant_data_path'])
        with open(fd, "w") as f:
            json.dump(devices, f)
        os.rename(filename, devices_path)

        next_scan = now + timedelta(seconds=scan_interval_seconds)
        logging.info("Next device discovery run scheduled for %s", next_scan)
        time.sleep(scan_interval_seconds)


def add_authentication_status(devices, settings):
    for device in devices:
        if not device["authenticationRequired"]:
            device["authenticated"] = True
            continue

        if device["type"] != "philips_hue":
            continue

        philips_hue_bridge_config_path = os.path.join(
            settings["homeassistant_data_path"],
            "{}.conf".format(device["id"]),
        )
        config = read_json(philips_hue_bridge_config_path, {})
        username = config.get(device["ip"], {}).get("username")

        api = PhilipsHueBridgeApiClient(device["ip"], username)
        device["authenticated"] = api.is_authenticated()


def add_homeassistant_entity_ids(devices):
    for device in devices:
        if device["type"] == "philips_hue":
            # TODO group has to be created manually for now
            device["ha_entity_id"] = "light.senic_hub_demo"
        else:
            room_name = device["extra"]["roomName"]
            device["ha_entity_id"] = "media_player.{}".format(room_name.replace(" ", "_").lower())
