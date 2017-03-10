import colander
import json
import logging
import os

from cornice.service import Service
from ..config import path
from ..subprocess_run import run


logger = logging.getLogger(__name__)


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
    fs_path = request.registry.settings['wifi_networks_path']
    if os.path.exists(fs_path):
        networks = json.load(open(fs_path))
        return list(networks.keys())
    else:
        return []


@wifi_setup.post(renderer='json', schema=JoinWifiSchema)
def join_network(request):
    ssid = request.validated['ssid']
    password = request.validated['password']
    logger.debug("Trying to connect to network '%s'", ssid)
    # TODO: Can we spawn the process so that we can give a proper request response?
    run([
        'sudo',
        os.path.join(request.registry.settings['bin_path'], 'join_wifi'),
        ssid,
        password,
    ])
    # TOOD: If we can still respond that probably means wifi wasn't joined,
    #       or that we were already connected to the same Wi-Fi.
    #       Study all possible case to return something helpful if possible.
    return {'error': 'failed'}
