from configparser import ConfigParser
from logging import getLogger
from os import path
from uuid import uuid4

from colander import MappingSchema, SchemaNode, String

from cornice.service import Service
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound

from ..config import path as service_path
from .setup_devices import get_device


logger = getLogger(__name__)


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

    def nuimo_app_config_component_to_response_component(device):
        component = {
            'component': device['component'],
            'device_id': device['device_id'],
        }
        if component['component'] == 'philips_hue':
            component['selected_devices'] = [d.strip() for d in device['lights'].split(',')]
        return component

    config = ConfigParser()
    config.read(nuimo_app_config_path)
    components = [
        nuimo_app_config_component_to_response_component(dict(config[s]))
        for s in config.sections()
    ]

    return {'components': components}


class AddComponentSchema(MappingSchema):
    device_id = SchemaNode(String())


@nuimo_components_service.post(schema=AddComponentSchema)
def add_nuimo_component_view(request):
    device_id = request.validated['device_id']

    device_list_path = request.registry.settings['devices_path']
    try:
        device = get_device(device_list_path, device_id)
    except HTTPNotFound:
        raise HTTPBadRequest

    component = create_component(device)

    with open(request.registry.settings['nuimo_app_config_path'], 'r+') as f:
        config = ConfigParser()
        config.read_file(f)
        component['index'] = len(config.sections())
        config[component['id']] = component
        f.seek(0)  # We want to overwrite the config file with the new configuration
        config.write(f)

    return component


def create_component(device):
    COMPONENT_FOR_TYPE = {
        'sonos': 'sonos',
        'soundtouch': 'media_player',
        'philips_hue': 'philips_hue',
    }
    component = {
        'id': str(uuid4()),
        'device_id': device['id'],
        'component': COMPONENT_FOR_TYPE[device['type']],
    }
    if component['component'] in ['philips_hue', 'sonos']:
        component['ip_address'] = device['ip']
    if component['component'] == 'philips_hue':
        component['username'] = device['extra']['username']
        component['lights'] = ", ".join(sorted(list(device['extra']['lights'])))
    return component


@nuimo_component_service.delete()
def delete_nuimo_component_view(request):
    component_id = request.matchdict["component_id"]
    with open(request.registry.settings['nuimo_app_config_path'], 'r+') as f:
        config = ConfigParser()
        config.read_file(f)
        if component_id not in config.sections():
            raise HTTPNotFound()
        config.remove_section(component_id)
        f.seek(0)  # We want to overwrite the config file with the new configuration
        f.truncate()
        config.write(f)
