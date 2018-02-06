from logging import getLogger
from os import path
from uuid import uuid4

from colander import Length, MappingSchema, SchemaNode, SequenceSchema, String

from cornice.service import Service
from cornice.validators import colander_body_validator
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound

from ..config import path as service_path
from .setup_devices import get_device
from .api_descriptions import descriptions as desc
from .nuimos import is_device_responsive

import yaml
import requests
import json
import time
import soco

logger = getLogger(__name__)


nuimo_components_service = Service(
    name='nuimo_components',
    path=service_path('nuimos/{mac_address:[a-z0-9\-]+}/components'),
    description=desc.get('nuimo_components_service'),
    renderer='json',
    accept='application/json',
)


nuimo_component_service = Service(
    name='nuimo_component',
    path=service_path('nuimos/{mac_address:[a-z0-9\-]+}/components/{component_id:[a-z0-9\-]+}'),
    description=desc.get('nuimo_component_service'),
    renderer='json',
    accept='application/json',
)


nuimo_device_test_service = Service(
    name='nuimo_device_test',
    path=service_path('nuimos/{mac_address:[a-z0-9\-]+}/components/{component_id:[a-z0-9\-]+}/test/{device_id:[a-z0-9\-]+}'),
    description=desc.get('nuimo_device_test_service'),
    renderer='json',
    accept='application/json'
)


@nuimo_components_service.get()
def nuimo_components_view(request):
    nuimo_app_config_path = request.registry.settings['nuimo_app_config_path']
    mac_address = request.matchdict['mac_address'].replace('-', ':')

    if not path.exists(nuimo_app_config_path):
        raise HTTPNotFound("App config file does not exist")

    def nuimo_app_config_component_to_response_component(component):
        return {
            'id': component['id'],
            'type': component['type'],
            'device_ids': component['device_ids'],
            'name': component['name']
        }

    with open(nuimo_app_config_path, 'r') as f:
        config = yaml.load(f)

    try:
        nuimo = config['nuimos'][mac_address]
    except (KeyError, TypeError):
        return HTTPNotFound("No Nuimo with such ID")

    components = [
        nuimo_app_config_component_to_response_component(c)
        for c in nuimo['components']
    ]

    return {'components': components}


class DeviceIdsSchema(SequenceSchema):
    device_id = SchemaNode(String())


class AddComponentSchema(MappingSchema):
    device_ids = DeviceIdsSchema(validator=Length(min=1))


@nuimo_components_service.post(schema=AddComponentSchema, validators=(colander_body_validator,))
def add_nuimo_component_view(request):
    device_ids = request.validated['device_ids']
    mac_address = request.matchdict['mac_address'].replace('-', ':')

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
        config = yaml.load(f)

        try:
            nuimo = config['nuimos'][mac_address]
        except (KeyError, TypeError):
            return HTTPNotFound("No Nuimo with such ID")

        group_number = [comp['name'] for comp in nuimo['components'] if " Group " in comp['name'] and component['ip_address'] in comp['name']]

        for comp in nuimo['components']:
            if component['name'] == comp['name'] and " Group " not in comp['name']:
                component['name'] = component['name'] + " Group " + str(len(group_number) + 1)
        nuimo['components'].append(component)
        f.seek(0)  # We want to overwrite the config file with the new configuration
        yaml.dump(config, f, default_flow_style=False)

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
        'philips_hue': 'philips_hue',
    }
    component_type = COMPONENT_FOR_TYPE[device['type']]
    component = {
        'id': str(uuid4()),
        'device_ids': [device['id']],
        'type': component_type,
        'name': device['name']
    }

    if component_type == 'sonos':
        component['ip_address'] = device['ip']

    if component_type == 'philips_hue':
        component['ip_address'] = device['ip']
        component['username'] = device['extra']['username']
        light_ids = sorted(list(device['extra']['lights']))
        light_ids = ['%s-light-%s' % (device['id'], i) for i in light_ids]
        component['device_ids'] = light_ids

    return component


@nuimo_component_service.get()
def get_nuimo_component_view(request):
    component_id = request.matchdict['component_id']
    mac_address = request.matchdict['mac_address'].replace('-', ':')
    with open(request.registry.settings['nuimo_app_config_path'], 'r') as f:
        config = yaml.load(f)

    try:
        nuimo = config['nuimos'][mac_address]
    except (KeyError, TypeError):
        return HTTPNotFound("No Nuimo with such ID")

    components = nuimo['components']
    try:
        return next(c for c in components if c['id'] == component_id)
    except StopIteration:
        raise HTTPNotFound


@nuimo_component_service.delete()
def delete_nuimo_component_view(request):
    component_id = request.matchdict['component_id']
    mac_address = request.matchdict['mac_address'].replace('-', ':')
    with open(request.registry.settings['nuimo_app_config_path'], 'r+') as f:
        config = yaml.load(f)

        try:
            nuimo = config['nuimos'][mac_address]
        except (KeyError, TypeError):
            return HTTPNotFound("No Nuimo with such ID")

        components = nuimo['components']

        try:
            component = next(c for c in components if c['id'] == component_id)
        except StopIteration:
            raise HTTPNotFound

        components.remove(component)

        f.seek(0)  # We want to overwrite the config file with the new configuration
        f.truncate()
        yaml.dump(config, f, default_flow_style=False)


class ModifyComponentSchema(MappingSchema):
    device_ids = DeviceIdsSchema(validator=Length(min=1))


@nuimo_component_service.put(schema=ModifyComponentSchema, validators=(colander_body_validator,))
def modify_nuimo_component(request):
    component_id = request.matchdict['component_id']
    mac_address = request.matchdict['mac_address'].replace('-', ':')
    # TODO: Validate `device_ids` if they map to the same device type as the component
    device_ids = request.validated['device_ids']

    with open(request.registry.settings['nuimo_app_config_path'], 'r+') as f:
        config = yaml.load(f)

        try:
            nuimo = config['nuimos'][mac_address]
        except (KeyError, TypeError):
            return HTTPNotFound("No Nuimo with such ID")

        components = nuimo['components']

        try:
            component = next(c for c in components if c['id'] == component_id)
        except StopIteration:
            raise HTTPNotFound

        # JOIN two SONOS Speakers
        if component['type'] == 'sonos' and (len(component['device_ids']) > 1 or len(device_ids) > 1):  # pragma: no cover,
            for device in device_ids:
                if device not in component['device_ids']:
                    try:
                        join_component = next(c for c in components if device in c['device_ids'])
                    except StopIteration:
                        raise HTTPNotFound
                    soco_instance = soco.SoCo(component['ip_address'])
                    soco_joining_instance = soco.SoCo(join_component['ip_address'])
                    if is_device_responsive(component['ip_address']) and is_device_responsive(join_component['ip_address']):
                        try:
                            soco_joining_instance.join(soco_instance)
                        except (requests.exceptions.RequestException, soco.SoCoException):
                            return HTTPNotFound("No Sonos with such ip address")
                        join_component['join'] = {'master': False, 'ip_address': component['ip_address']}
                        if component.get('join', None):
                            component['join'][join_component['ip_address']] = join_component['device_ids'][0]
                        else:
                            component['join'] = {'master': True, join_component['ip_address']: [join_component['device_ids'][0]]}
                    else:
                        return HTTPNotFound("Sonos device not reachable")
            for device in component['device_ids']:
                if device not in device_ids:
                    try:
                        unjoin_component = next(c for c in components if device in c['device_ids'] and c is not component)
                    except StopIteration:
                        raise HTTPNotFound
                    soco_unjoining_instance = soco.SoCo(unjoin_component['ip_address'])
                    if is_device_responsive(component['ip_address']) and is_device_responsive(unjoin_component['ip_address']):
                        try:
                            if soco_unjoining_instance.player_name != soco_unjoining_instance.group.coordinator.player_name:
                                soco_unjoining_instance.unjoin()
                        except (requests.exceptions.RequestException, soco.SoCoException):
                            return HTTPNotFound("Speaker is not unjoinable or not reachable")
                        del unjoin_component['join']
                        del component['join'][unjoin_component['ip_address']]
                    else:
                        return HTTPNotFound("Sonos device not reachable")

        component['device_ids'] = device_ids

        f.seek(0)  # We want to overwrite the config file with the new configuration
        f.truncate()
        yaml.dump(config, f, default_flow_style=False)

    return get_nuimo_component_view(request)


# Send a GET request in the form of HUB_URL/nuimos/<nuimo_mac_address>/components/<component_id>/test/<device_id>
# If device has no sub-device, <device_id> will be same as <device_id>
@nuimo_device_test_service.get()
def get_test_response(request):
    component_id = request.matchdict['component_id']
    mac_address = request.matchdict['mac_address'].replace('-', ':')
    device_id = request.matchdict['device_id']
    hub_ip = get_current_ip()

    nuimo_app_config_path = request.registry.settings['nuimo_app_config_path']

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
            return HTTPNotFound("Component :" + component_id + "for Nuimo :" + mac_address + " ---> Not Found")

    component_type = component['type']
    component_ip = component['ip_address']
    component_username = component.get('username', None)  # Not all components have a username (like Sonos)

    if component_type == "philips_hue":
        blink_result = test_blink_phue(component_ip, component_username, device_id)
        if blink_result is True:
            return {
                'test_component': component_type,
                'test_component_id': component_id,
                'test_device_id': str(device_id),
                'test_result': 'PASS',
                'message': 'BLINK_SUCCESSFUL'
            }

        else:
            return {
                'test_component': component_type,
                'test_component_id': component_id,
                'test_device_id': str(device_id),
                'test_result': 'FAIL',
                'message': 'ERROR_PHUE_PUT_REQUEST_FAIL'
            }

    if component_type == "sonos":  # pragma: no cover
        test_result = test_ring_sonos(component_ip, hub_ip)
        if test_result is True:
            return {
                'test_component': component_type,
                'test_component_id': component_id,
                'test_device_id': str(device_id),
                'test_result': 'PASS',
                'message': 'TEST_SUCCESSFUL'
            }
        else:
            return {
                'test_component': component_type,
                'test_component_id': component_id,
                'test_device_id': str(device_id),
                'test_result': 'FAIL',
                'message': 'ERROR_SONOS_TEST_PLAY_FAIL'
            }


def test_blink_phue(component_ip, component_username, id):
    device_id = id.split('-')[2]
    request_url_get_default = "http://" + component_ip + "/api/" + str(component_username) + "/lights/" + str(device_id)
    try:
        default_state = requests.get(request_url_get_default, timeout=1).json()
        state_default = default_state['state']['on']
        bri_default = default_state['state']['bri']

    except Exception as e:
        logger.error("Error while testing Sonos: " + str(e))
        return False

    param_high = json.dumps({
        "on": True,
        "bri": 250
    })
    param_low = json.dumps({
        "on": False,
        "bri": 0
    })
    param_default = json.dumps({
        "on": state_default,
        "bri": bri_default
    })
    request_url_put = "http://" + component_ip + "/api/" + str(component_username) + "/lights/" + str(device_id) + "/state"
    try:
        requests.put(request_url_put, data=param_high, timeout=1)
        time.sleep(0.5)
        requests.put(request_url_put, data=param_low, timeout=1)
        time.sleep(0.5)
        requests.put(request_url_put, data=param_default, timeout=1)
        return True

    except Exception as e:
        logger.error("Error while testing PHue: " + str(e))
        return False


def test_ring_sonos(component_ip, hub_ip):   # pragma: no cover
    test_speaker = soco.SoCo(component_ip)
    if hub_ip is None:
        logger.error("Unable to extract Hub IP Address.")
        return False
    # The lighttpd server is configured to listen on port 81
    # Resource files are stored in /www/pages/resources .. (on the hub)
    port = 80
    uri_test = "http://" + hub_ip + ":" + str(port) + "/resources/swblaster.mp3"
    try:
        test_speaker.volume = 10
        test_speaker.play_uri(uri_test)
        test_speaker.get_current_track_info()
        time.sleep(2)
        test_speaker.stop()
        try:
            test_speaker.play_from_queue(0)
            test_speaker.stop()
        except soco.SoCoException:
            # No action required, as the queue is empty.
            pass
        return True

    except (soco.SoCoException, HTTPNotFound) as e:
        logger.error("Error while testing Sonos: " + str(e))
        return False


def get_current_ip():  # pragma: no cover
    try:
        import NetworkManager
    except:
        logger.error("Unable to import NetworkManager")
        return None
    try:
        nm_devices = NetworkManager.NetworkManager.GetDevices()
        nm_device = dict([(d.Interface, d) for d in nm_devices])
    except AttributeError as e:
        logger.warning("Error while trying to get NetworkManager device : " + e)
        return None

    wlan_device = nm_device.get('wlan0', None)
    if not wlan_device:
        logger.error("Couldn't find the Network Adapter")
        return None

    if not wlan_device.Ip4Config:
        return None

    addr = wlan_device.Ip4Config.AddressData[0].get('address', None)
    logger.info("Updating IP Address of Hub to " + addr)
    return addr
