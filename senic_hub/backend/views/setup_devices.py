import json
import logging
import os
import os.path

from cornice.service import Service

from pyramid.httpexceptions import HTTPBadGateway, HTTPBadRequest, HTTPNotFound
from json.decoder import JSONDecodeError
from cornice.validators import colander_body_validator
from .. import supervisor

from ..config import path
from ..device_discovery import PhilipsHueBridgeApiClient, UnauthenticatedDeviceError, UpstreamError
from ..lockfile import open_locked
from .api_descriptions import descriptions as desc


logger = logging.getLogger(__name__)


list_service = Service(
    name='devices_list',
    path=path('setup/devices'),
    description=desc.get('list_service'),
    renderer='json',
)


@list_service.get()
def devices_list_view(request):
    """
    Returns list of discovered devices/bridges.

    """
    return read_json(request.registry.settings['devices_path'], [])


discover_service = Service(
    name='devices_discover',
    path=path('setup/devices/discover'),
    renderer='json',
    accept='application/json',
)


@discover_service.post(validators=(colander_body_validator,))
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


@authenticate_service.post(validators=(colander_body_validator,))
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

    senic_hub_data_path = request.registry.settings.get(
        "senic_hub_data_path", "/data/senic-hub"
    )
    phue_bridge_config = os.path.join(senic_hub_data_path, '{}.conf'.format(device["id"]))
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

    # Only Philips Hue has device details at the moment
    # TODO: In the future, each single Philips Hue light should be returned as a regular
    #       device. Philips Hue bridges should be flagged with `virtual: True` since they
    #       are not controlled by the user. However, all its lights should be returned as
    #       well when requesting `/devices`.
    if device['type'] != 'philips_hue':
        return {}

    senic_hub_data_path = request.registry.settings.get(
        "senic_hub_data_path", "/data/senic-hub"
    )
    phue_bridge_config = os.path.join(senic_hub_data_path, '{}.conf'.format(device["id"]))
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

    with open_locked(device_list_path, 'r') as f:
        devices = json.load(f)

    device = next((x for x in devices if x["id"] == device_id), None)
    if device is None:
        raise HTTPNotFound("Device with id = {} not found...".format(device_id))

    return device


def update_device(device, settings, username):  # pragma: no cover
    try:
        with open_locked(settings['devices_path'], 'r') as f:
            devices = json.loads(f.read())
    except (FileNotFoundError, JSONDecodeError):
        # if we don't have the devices.json file, there are no devices to
        # authenticate
        return

    device["extra"]["username"] = username

    if device['authenticated'] and username:
        bridge = PhilipsHueBridgeApiClient(device["ip"], username)

        device['extra']['lights'] = bridge.get_lights()

    device_index = [i for (i, d) in enumerate(devices) if d["id"] == device["id"]].pop()

    devices[device_index] = device

    with open_locked(settings['devices_path'], 'w') as f:
        json.dump(devices, f)


def read_json(file_path, default=None):
    try:
        with open_locked(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        return default
