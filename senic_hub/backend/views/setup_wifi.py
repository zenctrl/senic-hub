import colander
import json
import logging
import os
import re

from cornice.service import Service
from pyramid.httpexceptions import HTTPBadRequest
from subprocess import CalledProcessError, TimeoutExpired

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
    networks_path = request.registry.settings['wifi_networks_path']
    if os.path.exists(networks_path):
        with open(networks_path, "r") as networks_file:
            return json.load(networks_file)
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
    try:
        run([
            'sudo',
            os.path.join(request.registry.settings['bin_path'], 'wifi_setup'),
            '-c', request.registry.settings['config_ini_path'],
            'join',
            ssid,
            password
        ], check=True)
        logger.info("Joining network '%s' succeeded" % ssid)
    except CalledProcessError as e:
        logger.error("Failed to join network '%s'" % ssid)
        raise HTTPBadRequest()


@wifi_connection.get()
def get_wifi_connection(request):
    try:
        status = run([
            'sudo',
            os.path.join(request.registry.settings['bin_path'], 'wifi_setup'),
            '-c', request.registry.settings['config_ini_path'],
            'status'
        ]).stdout.decode('utf8')
    except TimeoutExpired:
        status = ""
    ssid_match = re.search("^infra_ssid=(.*)$", status, flags=re.MULTILINE)
    ssid = ssid_match.group(1) if ssid_match else None
    if 'infra_status=connecting' in status:
        status = 'connecting'
    elif 'infra_status=connected' in status:
        status = 'connected'
    else:
        status = 'unavailable'
    return dict(
        ssid=ssid if ssid else None,
        status=status
    )


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
