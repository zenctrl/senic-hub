import json
import logging
import os
import os.path

from tempfile import mkstemp

from cornice.service import Service

from pyramid.httpexceptions import HTTPBadGateway, HTTPBadRequest, HTTPNotFound
from pyramid.response import FileResponse

from .. import supervisor

from ..config import path
from ..device_discovery import PhilipsHueBridgeApiClient, UnauthenticatedDeviceError, UpstreamError, read_json


logger = logging.getLogger(__name__)


list_service = Service(
    name='devices_list',
    path=path('setup/devices'),
    renderer='json',
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


discover_service = Service(
    name='devices_discover',
    path=path('setup/devices/discover'),
    renderer='json',
    accept='application/json',
)


@discover_service.post()
def devices_discover_view(request):
    """
    Trigger device discovery daemon restart to force a new device
    scan.

    """
    logger.info("Restarting device discovery daemon...")
    supervisor.restart_program('device_discovery')


authenticate_service = Service(
    name='devices_authenticate',
    path=path('setup/devices/{device_id:[a-z0-9]+}/authenticate'),
    renderer='json',
    accept='application/json',
)


@authenticate_service.post()
def devices_authenticate_view(request):
    """
    NOTE: This view updates HASS configuration files. No locking is
    performed here.

    """
    device_id = request.matchdict["device_id"]
    logger.debug("Authenticating device with ID=%s", device_id)

    device_list_path = request.registry.settings['devices_path']
    device = get_device(device_list_path, device_id)
    if not device["authenticationRequired"]:
        return {"id": device_id, "authenticated": True}

    homeassistant_data_path = request.registry.settings["homeassistant_data_path"]
    phue_bridge_config = os.path.join(homeassistant_data_path, '{}.conf'.format(device["id"]))
    config = read_json(phue_bridge_config, {})
    username = config.get(device["ip"], {}).get("username")

    bridge = PhilipsHueBridgeApiClient(device["ip"], username)
    if not bridge.is_authenticated():
        username = bridge.authenticate()

    if username:
        config[device["ip"]] = {"username": username}
    else:
        config.pop(device["ip"], None)

    authenticated = username is not None
    device["authenticated"] = authenticated

    with open(phue_bridge_config, "w") as f:
        json.dump(config, f)

    update_device(device, request.registry.settings, username)

    return {"id": device_id, "authenticated": authenticated}


details_service = Service(
    name='devices_details',
    path=path('setup/devices/{device_id:(?!discover)[a-z0-9]+}'),
    renderer='json',
)


@details_service.get()
def devices_details_view(request):
    device_id = request.matchdict["device_id"]
    logger.debug("Getting details for device with ID=%s", device_id)

    device_list_path = request.registry.settings['devices_path']
    device = get_device(device_list_path, device_id)

    homeassistant_data_path = request.registry.settings["homeassistant_data_path"]
    phue_bridge_config = os.path.join(homeassistant_data_path, '{}.conf'.format(device["id"]))
    config = read_json(phue_bridge_config, {})
    username = config.get(device["ip"], {}).get("username")

    try:
        bridge = PhilipsHueBridgeApiClient(device["ip"], username)

        return bridge.get_lights()
    # TODO create a tween to handle exceptions for all views
    except UnauthenticatedDeviceError as e:
        raise HTTPBadRequest(e.message)
    except UpstreamError as e:
        raise HTTPBadGateway(e.message)


def get_device(device_list_path, device_id):
    if not os.path.exists(device_list_path):
        raise HTTPNotFound("Device discovery was not run...")

    with open(device_list_path, "r") as f:
        devices = json.loads(f.read())

    device = next((x for x in devices if x["id"] == device_id), None)
    if device is None:
        raise HTTPNotFound("Device with id = {} not found...".format(device_id))

    return device


def update_device(device, settings, username):
    devices_path = settings["devices_path"]
    with open(devices_path, "r") as f:
        devices = json.loads(f.read())

    device["extra"]["username"] = username

    if device['authenticated'] and username:
        bridge = PhilipsHueBridgeApiClient(device["ip"], username)

        device['extra']['lights'] = bridge.get_lights()

    device_index = [i for (i, d) in enumerate(devices) if d["id"] == device["id"]].pop()

    devices[device_index] = device

    fd, filename = mkstemp(dir=settings['homeassistant_data_path'])
    with open(fd, "w") as f:
        json.dump(devices, f)
    os.rename(filename, devices_path)
