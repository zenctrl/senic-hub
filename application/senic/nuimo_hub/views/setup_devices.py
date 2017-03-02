import json
import os

import colander

from cornice.service import Service

from pyramid.response import FileResponse

from ..config import path
from ..device_discovery import discover


list_service = Service(
    name='devices_list',
    path=path('setup/devices'),
    renderer='json',
)


class DevicesDiscoverSchema(colander.MappingSchema):
    pass


discover_service = Service(
    name='devices_discover',
    path=path('setup/devices/discover'),
    renderer='json',
    accept='application/json',
)


@list_service.get()
def devices_list_view(request):
    """
    Returns list of discovered devices/bridges.

    """
    fs_path = request.registry.settings['fs_device_list']

    if os.path.exists(fs_path):
        return FileResponse(fs_path, request)
    else:
        return dict()


@discover_service.post()
def devices_discover_view(request, schema=DevicesDiscoverSchema):
    """
    Discovers devices, writes results to a file and returns them in
    response.

    NOTE: Will block until device discovery is finished.

    """
    device_list_file = request.registry.settings['fs_device_list']

    discovered_devices = discover()
    with open(device_list_file, 'w') as f:
        json.dump(discovered_devices, f)

    return discovered_devices
