import json
import logging
import os

from cornice.service import Service

from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
from pyramid.response import FileResponse

from ..config import path
from ..device_discovery import PhilipsHueBridge, UnauthenticatedDeviceError, discover


logger = logging.getLogger(__name__)


list_service = Service(
    name='devices_list',
    path=path('setup/devices'),
    renderer='json',
)


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
    fs_path = request.registry.settings['devices_path']

    if os.path.exists(fs_path):
        return FileResponse(fs_path, request)
    else:
        return []


@discover_service.post()
def devices_discover_view(request):
    """
    Discovers devices, writes results to a file and returns them in
    response.

    NOTE: Will block until device discovery is finished.

    """
    device_list_file = request.registry.settings['devices_path']

    discovered_devices = discover()
    with open(device_list_file, 'w') as f:
        json.dump(discovered_devices, f)

    return discovered_devices


authenticate_service = Service(
    name='devices_authenticate',
    path=path('setup/devices/{device_id:\d+}/authenticate'),
    renderer='json',
    accept='application/json',
)


@authenticate_service.post()
def devices_authenticate_view(request):
    device_id = int(request.matchdict["device_id"])
    logger.debug("Authenticating device with ID=%s", device_id)

    device_list_path = request.registry.settings['devices_path']
    device = get_device(device_list_path, device_id)
    if device["type"] != "philips_hue":
        raise HTTPBadRequest("Device doesn't require authentication...")

    data_location = request.registry.settings.get("data_directory_path", "/tmp")
    bridge = PhilipsHueBridge(device["ip"], data_location)
    if not bridge.is_authenticated():
        logger.debug("Trying to authenticate Philips Hue bridge %s", device["ip"])
        bridge.authenticate()

    logger.debug("Philips Hue bridge %s authenticated: %s", device["ip"], bridge.is_authenticated())

    return {"id": device_id, "authenticated": bridge.is_authenticated()}


details_service = Service(
    name='devices_details',
    path=path('setup/devices/{device_id:\d+}'),
    renderer='json',
)


@details_service.get()
def devices_details_view(request):
    device_id = int(request.matchdict["device_id"])
    logger.debug("Getting details for device with ID=%s", device_id)

    device_list_path = request.registry.settings['devices_path']
    device = get_device(device_list_path, device_id)

    data_location = request.registry.settings.get("data_directory_path", "/tmp")
    bridge = PhilipsHueBridge(device["ip"], data_location)

    try:
        return bridge.get_lights()
    except UnauthenticatedDeviceError as e:
        raise HTTPBadRequest(e.message)


def get_device(device_list_path, device_id):
    if not os.path.exists(device_list_path):
        raise HTTPNotFound("Device discovery was not run...")

    with open(device_list_path, "r") as f:
        devices = json.loads(f.read())

    device = next((x for x in devices if x["id"] == device_id), None)
    if device is None:
        raise HTTPNotFound("Device with id = {} not found...".format(device_id))

    return device
