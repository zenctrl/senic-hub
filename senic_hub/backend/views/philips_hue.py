from cornice.service import Service
from logging import getLogger
# TODO: We better rename `config.path` to something else. Conflicts with `os.path`
from ..config import path as service_path
from pyramid.httpexceptions import HTTPNotFound
import yaml
import phue
from random import sample
import time
from ..device_discovery import PhilipsHueBridgeApiClient

from colander import MappingSchema, SchemaNode, String, Int, Range
from cornice.validators import colander_body_validator
from .api_descriptions import descriptions as desc
import requests

logger = getLogger(__name__)


nuimo_philips_hue_favorites = Service(
    name='nuimo_philips_hue_favorites',
    path=service_path('nuimos/{mac_address:[a-z0-9\-]+}/components/{component_id:[a-z0-9\-]+}/nuimophuefavs'),
    description=desc.get('nuimo_philips_hue_favorites'),
    renderer='json',
    accept='application/json')


philips_hue_favorites = Service(
    name='philips_hue_favorites',
    path=service_path('nuimos/{mac_address:[a-z0-9\-]+}/components/{component_id:[a-z0-9\-]+}/phuefavs'),
    description=desc.get('philips_hue_favorites'),
    renderer='json',
    accept='application/json')


test_philips_hue_favorite = Service(
    name='test_philips_hue_favorite',
    path=service_path('nuimos/{mac_address:[a-z0-9\-]+}/components/{component_id:[a-z0-9\-]+}/phuefavs/{favorite_id:[a-z0-9\-]+}'),
    description=desc.get('test_philips_hue_favorite'),
    renderer='json',
    accept='application/json')


@nuimo_philips_hue_favorites.get()
def get_nuimo_philips_hue_favorites(request):
    nuimo_app_config_path = request.registry.settings['nuimo_app_config_path']
    mac_address = request.matchdict['mac_address'].replace('-', ':')
    component_id = request.matchdict['component_id']

    with open(nuimo_app_config_path, 'r+') as f:
        config = yaml.load(f)

        try:
            nuimo = config['nuimos'][mac_address]
        except (KeyError, TypeError):
            return HTTPNotFound("No Nuimo with such ID")

        components = nuimo['components']

        try:
            component = next(c for c in components if c['id'] == component_id)
        except StopIteration:
            raise HTTPNotFound("No Component with such ID")

        if component['type'] != 'philips_hue':
            return HTTPNotFound("No Philips Hue Component with such ID")

        station1 = component.get('station1', None)
        station2 = component.get('station2', None)
        station3 = component.get('station3', None)
        scenes = {}

        if not any((station1, station2, station3)):
            philips_hue_bridge = PhilipsHueBridgeApiClient(component['ip_address'], component['username'])
            try:
                scenes = philips_hue_bridge.get_scene()
            except (ConnectionResetError, requests.exceptions.ConnectionError):
                logger.error("Hue Bridge not reachable, handle exception")

            light_ids = [device.split('-')[-1] for device in component['device_ids']]
            scenes = {k: v for k, v in scenes.items() if v['lights'] == light_ids}

            if len(list(scenes.keys())) >= 3:
                for scene in scenes:
                    component['station1'] = station1 = {'id': scene, 'name': scenes[scene]['name']} if scenes[scene]['name'] == 'Nightlight' else station1
                    component['station2'] = station2 = {'id': scene, 'name': scenes[scene]['name']} if scenes[scene]['name'] == 'Relax' else station2
                    component['station3'] = station3 = {'id': scene, 'name': scenes[scene]['name']} if scenes[scene]['name'] == 'Concentrate' else station3

                rands = sample(range(0, len(list(scenes.keys()))), 3)
                component['station1'] = station1 = {'id': list(scenes.keys())[rands[0]], 'name': scenes[list(scenes.keys())[rands[0]]]['name']} if station1 is None else station1
                component['station2'] = station2 = {'id': list(scenes.keys())[rands[1]], 'name': scenes[list(scenes.keys())[rands[1]]]['name']} if station2 is None else station2
                component['station3'] = station3 = {'id': list(scenes.keys())[rands[2]], 'name': scenes[list(scenes.keys())[rands[2]]]['name']} if station3 is None else station3
                f.seek(0)  # We want to overwrite the config file with the new configuration
                f.truncate()
                yaml.dump(config, f, default_flow_style=False)
            return {'station1': station1, 'station2': station2, 'station3': station3}
        else:
            philips_hue_bridge = PhilipsHueBridgeApiClient(component['ip_address'], component['username'])
            try:
                scenes = philips_hue_bridge.get_scene()
            except (ConnectionResetError, requests.exceptions.ConnectionError):
                logger.error("Hue Bridge not reachable, handle exception")
                return {'station1': None, 'station2': None, 'station3': None}

            light_ids = [device.split('-')[-1] for device in component['device_ids']]
            scenes = {k: v for k, v in scenes.items() if v['lights'] == light_ids}

            if scenes == {}:
                station1 = None
                station2 = None
                station3 = None

            return {'station1': station1, 'station2': station2, 'station3': station3}


class itemSchema(MappingSchema):
    id = SchemaNode(String())
    name = SchemaNode(String())


class PutPhueFavSchema(MappingSchema):
    number = SchemaNode(Int(), validator=Range(1, 3))
    item = itemSchema()


@nuimo_philips_hue_favorites.put(schema=PutPhueFavSchema, validators=(colander_body_validator,))
def put_nuimo_philips_hue_favorite(request):
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

        if component['type'] != 'philips_hue':
            return HTTPNotFound("No Philips Hue Component with such ID")

        component['station' + str(number)] = item

        f.seek(0)  # We want to overwrite the config file with the new configuration
        f.truncate()
        yaml.dump(config, f, default_flow_style=False)


@philips_hue_favorites.get()
def get_philips_hue_favorites(request):  # pragma: no cover,
    nuimo_app_config_path = request.registry.settings['nuimo_app_config_path']
    mac_address = request.matchdict['mac_address'].replace('-', ':')
    component_id = request.matchdict['component_id']

    with open(nuimo_app_config_path, 'r') as f:
        config = yaml.load(f)

    try:
        nuimo = config['nuimos'][mac_address]
    except (KeyError, TypeError):
        return HTTPNotFound("No Nuimo with such ID")

    components = nuimo['components']

    try:
        component = next(c for c in components if c['id'] == component_id)
    except StopIteration:
        raise HTTPNotFound("No Component with such ID")

    if component['type'] != 'philips_hue':
        return HTTPNotFound("No Philips Hue Component with such ID")

    philips_hue_bridge = phue.Bridge(component['ip_address'], component['username'])
    try:
        scenes = philips_hue_bridge.get_scene()
    except ConnectionResetError:
        return HTTPNotFound("Philips Hue Device not reachable")

    light_ids = [device.split('-')[-1] for device in component['device_ids']]
    scenes = {k: v for k, v in scenes.items() if v['lights'] == light_ids}

    if len(list(scenes.keys())) == 0:
        logger.info("no Philips Hue scenes")
        return {'favorites': []}

    scenes_list = []
    for scene in scenes:
        scenes[scene]['id'] = scene
        scenes_list.append(scenes[scene])

    return {'favorites': scenes_list}


@test_philips_hue_favorite.get()
def get_test_philips_hue_favorite(request):  # pragma: no cover,
    nuimo_app_config_path = request.registry.settings['nuimo_app_config_path']
    mac_address = request.matchdict['mac_address'].replace('-', ':')
    component_id = request.matchdict['component_id']
    favorite_id = request.matchdict['favorite_id']
    l = favorite_id.split('-')
    l = [c.capitalize() for c in l]
    l[0] = l[0].lower()
    favorite_id = ''.join(l)

    with open(nuimo_app_config_path, 'r') as f:
        config = yaml.load(f)

    try:
        nuimo = config['nuimos'][mac_address]
    except (KeyError, TypeError):
        return HTTPNotFound("No Nuimo with such ID")

    components = nuimo['components']

    try:
        component = next(c for c in components if c['id'] == component_id)
    except StopIteration:
        raise HTTPNotFound("No Component with such ID")

    if component['type'] != 'philips_hue':
        return HTTPNotFound("No Philips Hue Component with such ID")

    philips_hue_bridge = phue.Bridge(component['ip_address'], component['username'])
    try:
        philips_hue_bridge.activate_scene('0', favorite_id)
        time.sleep(1)
        group = phue.Group(philips_hue_bridge, 0)
        group.on = False
    except ConnectionResetError:
        return HTTPNotFound("Philips Hue Device not reachable")

    return {'result': 'OK'}
