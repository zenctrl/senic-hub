from cornice.service import Service
from logging import getLogger
# TODO: We better rename `config.path` to something else. Conflicts with `os.path`
from ..config import path as service_path
from pyramid.httpexceptions import HTTPNotFound
import yaml
from soco import SoCo, SoCoException

from colander import MappingSchema, SchemaNode, String, Int, Range
from cornice.validators import colander_body_validator
from .api_descriptions import descriptions as desc

logger = getLogger(__name__)


nuimo_sonos_favorites = Service(
    name='nuimo_sonos_favorites',
    path=service_path('nuimos/{mac_address:[a-z0-9\-]+}/components/{component_id:[a-z0-9\-]+}/nuimosonosfavs'),
    description=desc.get('nuimo_sonos_favorites'),
    renderer='json',
    accept='application/json')


sonos_favorites = Service(
    name='sonos_favorites',
    path=service_path('nuimos/{mac_address:[a-z0-9\-]+}/components/{component_id:[a-z0-9\-]+}/sonosfavs'),
    description=desc.get('sonos_favorites'),
    renderer='json',
    accept='application/json')


@nuimo_sonos_favorites.get()
def get_nuimo_sonos_favorites(request):
    nuimo_app_config_path = request.registry.settings['nuimo_app_config_path']
    mac_address = request.matchdict['mac_address'].replace('-', ':')
    component_id = request.matchdict['component_id']

    with open(nuimo_app_config_path, 'r+') as f:
        config = yaml.load(f)

        try:
            nuimo = config['nuimos'][mac_address]
        except KeyError:
            return HTTPNotFound("No Nuimo with such ID")

        components = nuimo['components']

        try:
            component = next(c for c in components if c['id'] == component_id)
        except StopIteration:
            raise HTTPNotFound("No Component with such ID")

        if component['type'] != 'sonos':
            return HTTPNotFound("No Sonos Component with such ID")

        station1 = component.get('station1', None)
        station2 = component.get('station2', None)
        station3 = component.get('station3', None)

        if not any((station1, station2, station3)):  # pragma: no cover,
            sonos_controller = SoCo(component['ip_address'])
            try:
                favorites = sonos_controller.get_sonos_favorites(max_items=3)
            except SoCoException:
                return HTTPNotFound("Sonos Device not reachable")

            if favorites['returned'] < 3:
                return HTTPNotFound("less than Three Favorites on Sonos")

            station1 = component['station1'] = favorites['favorites'][0]
            station2 = component['station2'] = favorites['favorites'][1]
            station3 = component['station3'] = favorites['favorites'][2]
            f.seek(0)  # We want to overwrite the config file with the new configuration
            f.truncate()
            yaml.dump(config, f, default_flow_style=False)

    return {'station1': station1, 'station2': station2, 'station3': station3}


class itemSchema(MappingSchema):
    uri = SchemaNode(String())
    meta = SchemaNode(String())
    title = SchemaNode(String())


class PutSonosFavSchema(MappingSchema):
    number = SchemaNode(Int(), validator=Range(1, 3))
    item = itemSchema()


@nuimo_sonos_favorites.put(schema=PutSonosFavSchema, validators=(colander_body_validator,))
def put_nuimo_sonos_favorite(request):
    nuimo_app_config_path = request.registry.settings['nuimo_app_config_path']
    mac_address = request.matchdict['mac_address'].replace('-', ':')
    component_id = request.matchdict['component_id']
    item = request.validated['item']
    number = request.validated['number']

    with open(nuimo_app_config_path, 'r+') as f:
        config = yaml.load(f)

        try:
            nuimo = config['nuimos'][mac_address]
        except KeyError:
            return HTTPNotFound("No Nuimo with such ID")

        components = nuimo['components']

        try:
            component = next(c for c in components if c['id'] == component_id)
        except StopIteration:
            raise HTTPNotFound("No Component with such ID")

        if component['type'] != 'sonos':
            return HTTPNotFound("No Sonos Component with such ID")

        component['station' + str(number)] = item

        f.seek(0)  # We want to overwrite the config file with the new configuration
        f.truncate()
        yaml.dump(config, f, default_flow_style=False)


@sonos_favorites.get()
def get_sonos_favorites(request):  # pragma: no cover,
    nuimo_app_config_path = request.registry.settings['nuimo_app_config_path']
    mac_address = request.matchdict['mac_address'].replace('-', ':')
    component_id = request.matchdict['component_id']

    with open(nuimo_app_config_path, 'r') as f:
        config = yaml.load(f)

    try:
        nuimo = config['nuimos'][mac_address]
    except KeyError:
        return HTTPNotFound("No Nuimo with such ID")

    components = nuimo['components']

    try:
        component = next(c for c in components if c['id'] == component_id)
    except StopIteration:
        raise HTTPNotFound("No Component with such ID")

    if component['type'] != 'sonos':
        return HTTPNotFound("No Sonos Component with such ID")

    sonos_controller = SoCo(component['ip_address'])
    try:
        favorites = sonos_controller.get_sonos_favorites()
    except SoCoException:
        return HTTPNotFound("Sonos Device not reachable")

    if favorites['returned'] < 3:
        return HTTPNotFound("less than Three Favorites on Sonos")

    return {'favorites': favorites}
