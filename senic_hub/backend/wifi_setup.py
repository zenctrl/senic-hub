import click
import json
import os
import re
import time

from os.path import abspath
from subprocess import TimeoutExpired
from .subprocess_run import run

import wifi
from pyramid.paster import get_app


INTERFACESD_WLAN_INFRA_PATH = '/etc/network/interfaces.d/wlan_infra'
INTERFACESD_WLAN_INFRA_SCAN_ONLY = '''
auto wlan1
iface wlan1 inet static
  address 10.0.42.42
  netmask 255.255.255.0
'''
INTERFACESD_WLAN_INFRA_JOIN = '''
auto wlan1
iface wlan1 inet dhcp
wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
'''

WPA_SUPPLICANT_CONF_PATH = '/etc/wpa_supplicant/wpa_supplicant.conf'
WPA_SUPPLICANT_CONF_TEMPLATE = '''
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
network={{
    ssid="{ssid}"
    psk="{password}"
}}
'''


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
        wpa_status = run(['wpa_cli', '-i', wlan_infra, 'status'], timeout=5).stdout.decode()
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

    click.echo("Restarting avahi daemon")
    # TODO: Check if we can control avahi via supervisor (if it's not tied too much with the system)
    # TODO: Send SIGHUP signal to ask avavahi daemon to reload its config
    run(['/bin/systemctl', 'restart', 'avahi-daemon'])
    click.echo("Wifi setup mode successfully entered")


def activate_adhoc(device):
    run(['ifup', device])


def activate_infra(device, ssid, password, timeout=None):
    """Throws `subprocess.TimeoutExpired` if `ifup` takes longer than `timeout`"""
    run(['ifdown', device])
    with open(INTERFACESD_WLAN_INFRA_PATH, 'w') as wlan_conf:
        if ssid:
            wlan_conf.write(INTERFACESD_WLAN_INFRA_JOIN)
        else:
            wlan_conf.write(INTERFACESD_WLAN_INFRA_SCAN_ONLY)
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
    click.echo("Configuring '%s' for infrastructure mode" % device)
    try:
        activate_infra(device, ssid, password, timeout=60)
        connected = False
        while True:
            click.echo("Requesting infrastructure connection state")
            status = run([
                os.path.join(ctx.obj['bin_path'], 'wifi_setup'),
                '-c', ctx.obj['config_ini_path'],
                'status'
            ]).stdout.decode()
            connected = 'infra_status=connected' in status
            if 'infra_status=connecting' not in status:
                break
    except TimeoutExpired:
        click.echo("Timeout while trying to connect to network")
        connected = False

    if connected:
        try:
            os.remove(ctx.obj['wifi_setup_flag_path'])
        except FileNotFoundError:
            pass
        # TODO: Send SIGHUP signal to ask avavahi daemon to reload its config
        run(['/bin/systemctl', 'restart', 'avahi-daemon'])
        click.echo("Joining wifi network '%s' succeeded" % ssid)
        exit(0)
    else:
        click.echo("Failed to join network '%s'" % ssid)
        exit(1)


@click.command(help='scan the wifi interfaces for networks (requires root privileges)')
@click.option('--config', '-c', required=True, type=click.Path(exists=True), help='app configuration file')
@click.option('--forever/--no-forever', default=False, help='scan forever (until interrupted)')
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
