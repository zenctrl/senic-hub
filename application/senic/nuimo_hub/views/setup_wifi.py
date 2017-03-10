import json
import os
from cornice.service import Service
import colander

from ..config import path
from ..subprocess_run import run


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
        'wifi_networks_path', 'wifi_networks.json')
    if os.path.exists(fs_path):
        networks = json.load(open(fs_path))
        return list(networks.keys())
    else:
        return []


@wifi_setup.post(renderer='json', schema=JoinWifiSchema)
def join_network(request):
    run([
        'sudo',
        os.path.join(request.registry.settings['bin_path'], 'join_wifi'),
        request.validated['ssid'],
        request.validated['password'],
    ])
