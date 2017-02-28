import os
from cornice.service import Service
from pyramid.response import FileResponse

from ..config import path


wifi_setup = Service(
    name='wifi_setup',
    path=path('/setup/wifi'),
    renderer='json',
    accept='application/json')


@wifi_setup.get()
def scan_wifi_networks(request):
    fs_path = request.registry.settings.get(
        'fs_wifi_networks', 'wifi_networks.json')
    if os.path.exists(fs_path):
        return FileResponse(fs_path, request)
    else:
        return dict()


@wifi_setup.post()
def join_network(request):
    pass
