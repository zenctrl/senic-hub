from configparser import ConfigParser
from logging import getLogger
from os import path
from uuid import uuid4

from colander import Length, MappingSchema, SchemaNode, SequenceSchema, String

from cornice.service import Service
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound

from ..config import path as service_path
from .setup_devices import get_device


logger = getLogger(__name__)


HOME_ASSISTANT_COMPONENT_TYPES = {'light', 'media_player'}


nuimo_components_service = Service(
    name='nuimo_components',
    path=service_path('nuimos/{nuimo_id:[a-z0-9]+}/components'),
    renderer='json',
    accept='application/json',
)


nuimo_component_service = Service(
    name='nuimo_component',
    path=service_path('nuimos/{nuimo_id:[a-z0-9]+}/components/{component_id:[a-z0-9\-]+}'),
    renderer='json',
    accept='application/json',
)


@nuimo_components_service.get()
def nuimo_components_view(request):
    nuimo_app_config_path = request.registry.settings['nuimo_app_config_path']

    if not path.exists(nuimo_app_config_path):
        raise HTTPNotFound("App config file does not exist")

    def nuimo_app_config_component_to_response_component(component_id, device):
        component = {
            'id': component_id,
            'type': device['type'],
            'device_ids': device['device_ids'].split(', '),
        }
        return component

    config = ConfigParser()
    config.read(nuimo_app_config_path)
    components = [
        nuimo_app_config_component_to_response_component(s, dict(config[s]))
        for s in config.sections()
    ]

    return {'components': components}


class DeviceIdsSchema(SequenceSchema):
    device_id = SchemaNode(String())


class AddComponentSchema(MappingSchema):
    device_ids = DeviceIdsSchema(validator=Length(min=1))


@nuimo_components_service.post(schema=AddComponentSchema)
def add_nuimo_component_view(request):
    device_ids = request.validated['device_ids']

    # TODO: We should check if all devices belong to the same type
    #       Right now it's not necessary as we expect proper API usage
    device_id = next(iter(device_ids))

    # Special case for Philips Hue: we obtain the bridge's device ID if light IDs are passed
    # We do this because `devices.json` doesn't store lights as single devices
    if '-light-' in device_id:
        device_id = device_id.split('-light-')[0]

    device_list_path = request.registry.settings['devices_path']
    try:
        device = get_device(device_list_path, device_id)
    except HTTPNotFound:
        raise HTTPBadRequest

    component = create_component(device)
    component['device_ids'] = device_ids

    with open(request.registry.settings['nuimo_app_config_path'], 'r+') as f:
        config = ConfigParser()
        config.read_file(f)
        config[component['id']] = component_to_app_config_component(component)
        f.seek(0)  # We want to overwrite the config file with the new configuration
        config.write(f)

    component['index'] = len(config.sections()) - 1

    return component


def create_component(device):
    """
    Takes a device dictionary as retrieved from `devices.json` and returns
    a component dictionary to be consumed by Nuimo app or to be returned by
    the devices API.

    Although Philips Hue lights are treated as single devices by the device
    API, this method can only consume Philips Hue Bridge devices from
    `devices.json`. Hence if you want to create a component with a selection
    of Philips Hue lights, you need to first create a component for the
    bridge itself. This method then returns and Hue component that selects
    all lights. If you only want to have specific lights selected, override
    the values for the `device_ids` key after retrieving the component.
    """
    COMPONENT_FOR_TYPE = {
        'sonos': 'sonos',
        'soundtouch': 'media_player',
        'philips_hue': 'philips_hue',
    }
    component_type = COMPONENT_FOR_TYPE[device['type']]
    component = {
        'id': str(uuid4()),
        'device_ids': [device['id']],
        'type': component_type,
    }
    if component_type in ['philips_hue', 'sonos']:
        component['ip_address'] = device['ip']
    if component_type == 'philips_hue':
        component['username'] = device['extra']['username']
        light_ids = sorted(list(device['extra']['lights']))
        light_ids = ['%s-light-%s' % (device['id'], i) for i in light_ids]
        component['device_ids'] = light_ids
    if component_type in HOME_ASSISTANT_COMPONENT_TYPES:
        component['ha_entity_id'] = device['ha_entity_id']
    return component


def component_to_app_config_component(component):
    app_config_component = {
        k: v for k, v in component.items()
        if k in ['ha_entity_id', 'id', 'ip_address', 'port', 'type', 'username']}
    app_config_component['device_ids'] = ', '.join(component['device_ids'])
    return app_config_component


def app_config_component_to_component(app_config_component):
    component = {
        k: v for k, v in app_config_component.items()
        if k in ['ha_entity_id', 'id', 'ip_address', 'port', 'type', 'username']}
    component['device_ids'] = app_config_component['device_ids'].split(', ')
    return component


@nuimo_component_service.get()
def get_nuimo_component_view(request):
    component_id = request.matchdict['component_id']
    with open(request.registry.settings['nuimo_app_config_path'], 'r+') as f:
        config = ConfigParser()
        config.read_file(f)
        try:
            app_config_component = dict(config[component_id])
        except KeyError:
            raise HTTPNotFound
    component = app_config_component_to_component(app_config_component)
    component['id'] = component_id
    return component


@nuimo_component_service.delete()
def delete_nuimo_component_view(request):
    component_id = request.matchdict['component_id']
    with open(request.registry.settings['nuimo_app_config_path'], 'r+') as f:
        config = ConfigParser()
        config.read_file(f)
        if component_id not in config.sections():
            raise HTTPNotFound()
        config.remove_section(component_id)
        f.seek(0)  # We want to overwrite the config file with the new configuration
        f.truncate()
        config.write(f)


class ModifyComponentSchema(MappingSchema):
    device_ids = DeviceIdsSchema(validator=Length(min=1))


@nuimo_component_service.put(schema=ModifyComponentSchema)
def modify_nuimo_component(request):
    component_id = request.matchdict['component_id']
    # TODO: Validate `device_ids` if they map to the same device type as the component
    device_ids = request.validated['device_ids']

    with open(request.registry.settings['nuimo_app_config_path'], 'r+') as f:
        config = ConfigParser()
        config.read_file(f)
        try:
            config[component_id]['device_ids'] = ', '.join(device_ids)
        except KeyError:
            raise HTTPNotFound
        f.seek(0)  # We want to overwrite the config file with the new configuration
        f.truncate()
        config.write(f)

    return get_nuimo_component_view(request)
