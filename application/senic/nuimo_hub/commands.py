import click
import json
import wifi

from os.path import abspath
from pyramid.paster import get_app


def get_networks(devices=['wlan0', 'wlan1']):
    networks = dict()
    for device in devices:
        networks.update({c.ssid: dict(device=device, cell=c) for c in wifi.Cell.all(device)})
    return networks


@click.command(help='scan the wifi interfaces for networks (requires root privileges)')
@click.option('--config', '-c', default='development.ini', help='app configuration file')
@click.argument('devices', nargs=-1)
def scan_wifi(config, devices):
    if devices == ():
        devices = ['wlan0', 'wlan1']
    networks = get_networks(devices=devices)
    json_networks = {n['cell'].ssid: dict(device=n['device']) for n in networks.values()}
    app = get_app(abspath(config))
    with open(app.registry.settings['fs_wifi_networks'], 'w') as wifi_file:
        json.dump(json_networks, wifi_file)


@click.command(help='join a given wifi network (requires root privileges)')
@click.argument('ssid')
@click.argument('password')
@click.argument('device')
def join_wifi(ssid, password, device):
    networks = get_networks(devices=[device])
    # TODO: allow for network no longer existing (between discovery and activation)
    cell = networks[ssid]['cell']
    # make sure we delete an existing scheme
    # this allows us to overwrite it, i.e. when a user
    # has provided the wrong password the first time round
    scheme = wifi.Scheme.find(device, 'default')
    if scheme is not None:
        scheme.delete()
    scheme = wifi.Scheme.for_cell(device, 'default', cell, password)
    scheme.save()
    scheme.activate()

