import click
import json
import os

from os.path import abspath
from subprocess import run, PIPE, TimeoutExpired

import wifi
from pyramid.paster import get_app


DEFAULT_IFACE = 'wlan0'
IFACES_AVAILABLE = '/etc/network/interfaces.available/{}'
IFACES_D = '/etc/network/interfaces.d/{}'
ENTER_SETUP_FLAG = '/var/run/NUIMO_SETUP_REQUIRED'

WPA_SUPPLICANT_FS = '/etc/wpa_supplicant/wpa_supplicant.conf'
WPA_SUPPLICANT_CONF = '''ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
network={{
    ssid="{ssid}"
    psk="{password}"
}}
'''


def get_networks(devices=[DEFAULT_IFACE]):
    networks = dict()
    for device in devices:
        networks.update({c.ssid: dict(device=device, cell=c) for c in wifi.Cell.all(device)})
    return networks


@click.command(help='scan the wifi interfaces for networks (requires root privileges)')
@click.option('--config', '-c', default='development.ini', help='app configuration file')
@click.argument('devices', nargs=-1)
def scan_wifi(config, devices):
    if devices == ():
        devices = [DEFAULT_IFACE]
    networks = get_networks(devices=devices)
    json_networks = {n['cell'].ssid: dict(device=n['device']) for n in networks.values()}
    app = get_app(abspath(config))
    with open(app.registry.settings['fs_wifi_networks'], 'w') as wifi_file:
        json.dump(json_networks, wifi_file)


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
@click.argument('device', default=DEFAULT_IFACE)
def enter_wifi_setup(device=DEFAULT_IFACE):
    if not os.path.exists(ENTER_SETUP_FLAG):
        exit(0)
    activate_adhoc(device)
    run(['/usr/bin/supervisorctl', 'start', 'dhcpd'])


@click.command(help='join a given wifi network (requires root privileges)')
@click.argument('ssid')
@click.argument('password')
@click.argument('device', default=DEFAULT_IFACE)
def join_wifi(ssid, password, device=DEFAULT_IFACE):
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

    if success:
        # clean up after ourselves
        if os.path.exists(ENTER_SETUP_FLAG):
            os.remove(ENTER_SETUP_FLAG)
        click.echo("Success!")
        exit(0)
    else:
        click.echo("Could not join %s." % ssid)
        exit(1)
