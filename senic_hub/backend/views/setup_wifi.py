import colander
import json
import logging
import os

from cornice.service import Service
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.response import FileResponse
from subprocess import CalledProcessError

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


wifi_connection = Service(
    name='wifi_connection',
    path=path('setup/wifi/connection'),
    renderer='json',
    accept='application/json')


@wifi_connection.post(renderer='json', schema=JoinWifiSchema)
def join_network(request):
    ssid = request.validated['ssid']
    password = request.validated['password']
    logger.debug("Trying to connect to network '%s'", ssid)
    # TODO: Can we spawn the process so that we can give a proper request response?
    try:
        run([
            'sudo',
            os.path.join(request.registry.settings['bin_path'], 'join_wifi'),
            '-c', request.registry.settings['config_ini_path'],
            ssid,
            password,
        ],
        check=True)
    except CalledProcessError:
        run([
            'sudo',
            os.path.join(request.registry.settings['bin_path'], 'enter_wifi_setup'),
            '-c', request.registry.settings['config_ini_path']
        ])
        # TOOD: If we can still respond that probably means wifi wasn't joined,
        #       or that we were already connected to the same Wi-Fi.
        #       Study all possible case to return something helpful if possible.
        raise HTTPBadRequest()


@wifi_connection.get()
def get_wifi_connection(request):
    fs_path = request.registry.settings['joined_wifi_path']
    if os.path.exists(fs_path):
        return FileResponse(fs_path)
    else:
        return dict(ssid=None, status='unavailable')


wifi_adhoc = Service(
    name='wifi_adhoc',
    path=path('setup/wifi/adhoc'),
    renderer='json',
    accept='application/json')


@wifi_adhoc.get()
def get_wifi_adhoc(request):
    return dict(
        ssid=request.registry.settings['wifi_adhoc_ssid'],
        status=os.path.exists(request.registry.settings['wifi_setup_flag_path']) and 'available' or 'unavailable')
