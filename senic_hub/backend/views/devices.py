from json import load as load_json
from logging import getLogger

from cornice.service import Service

from ..config import path as service_path
from .api_descriptions import descriptions as desc
from cornice.validators import colander_body_validator


logger = getLogger(__name__)


devices_service = Service(
    name='devices',
    path=service_path('devices'),
    description=desc.get('devices_service'),
    renderer='json',
    accept='application/json',
)


@devices_service.get(validators=(colander_body_validator,))
def nuimo_components_view(request):
    devices_path = request.registry.settings['devices_path']

    try:
        with open(devices_path) as f:
            raw_devices = load_json(f)
        devices = [expand_devices(d) for d in raw_devices]
        devices = [item for sub_devices in devices for item in sub_devices]
        devices.sort(key=lambda d: d['id'])
    except FileNotFoundError:
        devices = []

    return {'devices': devices}


def expand_devices(raw_device):
    """
    Some devices contain sub-devices, i.e. a Philips Hue bridge contains lights.
    This method expands such devices and returns the device itself and its
    contained devices as a list.

    """
    device = {k: v for k, v in raw_device.items() if k in {
        'id',
        'type',
        'ip',
        'port',
        'name',
        'authenticationRequired',
        'authenticated'
    }}
    # TODO: return user name as credentials

    if raw_device['type'] == 'philips_hue':
        device['virtual'] = True
        lights = raw_device['extra'].get('lights', {}).items()
        extra_devices = [{
            'id': '%s-light-%s' % (raw_device['id'], light_id),
            'type': 'philips_hue',
            'name': light['name'],
        } for (light_id, light) in lights]
    else:
        extra_devices = []

    return [device] + extra_devices
