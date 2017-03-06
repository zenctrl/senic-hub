import json
import os
from subprocess import run
from cornice.service import Service
import colander

from ..config import path


class JoinWifiSchema(colander.MappingSchema):
    ssid = colander.SchemaNode(colander.String())
    password = colander.SchemaNode(colander.String())


wifi_setup = Service(
    name='wifi_setup',
    path=path('setup/wifi'),
    renderer='json',
    accept='application/json')


@wifi_setup.get()
def scan_wifi_networks(request):
    fs_path = request.registry.settings.get(
        'fs_wifi_networks', 'wifi_networks.json')
    if os.path.exists(fs_path):
        networks = json.load(open(fs_path))
        return list(networks.keys())
    else:
        return []


@wifi_setup.post(renderer='json', schema=JoinWifiSchema)
def join_network(request):
    run([
        'sudo',
        os.path.join(request.registry.settings['fs_bin'], 'join_wifi'),
        request.validated['ssid'],
        request.validated['password'],
    ])
