from cornice.service import Service
from logging import getLogger
from os import path, system
from .. import nuimo_setup
# TODO: We better rename `config.path` to something else. Conflicts with `os.path`
from cornice.validators import colander_body_validator
# import colander

from ..config import path as service_path
from pyramid.httpexceptions import HTTPNotFound
import yaml
from .. import supervisor

from .api_descriptions import descriptions as desc
from colander import MappingSchema, String, SchemaNode, Length

import mmap
import os
import struct

import soco
import requests
from nuimo import Controller, ControllerManager

logger = getLogger(__name__)


connected_nuimos = Service(
    name='connected_nuimos',
    path=service_path('nuimos'),
    description=desc.get('connected_nuimos'),
    renderer='json',
    accept='application/json')


configured_nuimos = Service(
    name='configured_nuimos',
    path=service_path('confnuimos'),
    description=desc.get('configured_nuimos'),
    renderer='json',
    accept='application/json')


nuimo_service = Service(
    name='nuimo_services',
    path=service_path('nuimos/{mac_address:[a-z0-9\-]+}'),
    description=desc.get('nuimo_service'),
    renderer='json',
    accept='application/json',
)


check_for_update_service = Service(
    name='check_for_update_service',
    path=service_path('update'),
    renderer='json',
    accept='application/json',
)


@connected_nuimos.post(validators=(colander_body_validator,))
def bootstrap_nuimos(request):  # pragma: no cover,

    # [Alan] Backup for production to stop on a single nuimo
    output_filepath = request.registry.settings['nuimo_mac_address_filepath']
    if os.path.isfile(output_filepath):
        logger.info("You can't add another nuimo in this version")
        return get_connected_nuimos(request)

    adapter_name = request.registry.settings.get('bluetooth_adapter_name', 'hci0')
    required_mac_address = request.registry.settings.get('nuimo_mac_address')
    setup = nuimo_setup.NuimoSetup(adapter_name=adapter_name)
    mac_address = setup.discover_and_connect_controller(required_mac_address=required_mac_address, timeout=20)

    logger.info("Discovered and connected Nuimo: %s", mac_address)

    if mac_address:
        output_filepath = request.registry.settings['nuimo_mac_address_filepath']
        logger.debug("Write MAC address to %s", output_filepath)
        with open(output_filepath, 'w') as output_file:
            output_file.write(mac_address + '\n')

    return get_connected_nuimos(request)


@connected_nuimos.get()
def get_connected_nuimos(request):
    nuimo_mac_address_filepath = request.registry.settings.get('nuimo_mac_address_filepath')
    if not path.exists(nuimo_mac_address_filepath):
        return {'nuimos': []}
    with open(nuimo_mac_address_filepath, 'r') as nuimo_mac_address_file:
        mac_address = nuimo_mac_address_file.readline().strip()
        return {'nuimos': [mac_address.replace(':', '-')]}


@configured_nuimos.get()
def get_configured_nuimos(request):  # pragma: no cover,
    nuimo_app_config_path = request.registry.settings['nuimo_app_config_path']
    nuimos = []

    try:
        with open(nuimo_app_config_path, 'r+') as f:
            config = yaml.load(f)
            adapter_name = request.registry.settings.get('bluetooth_adapter_name', 'hci0')
            manager = ControllerManager(adapter_name=adapter_name)
            for mac_address in config['nuimos']:
                # check Nuimo connection Status
                controller = Controller(mac_address=mac_address, manager=manager)
                config['nuimos'][mac_address]['is_connected'] = controller.is_connected()

                # check if New Sonos Groups have been created
                components = config['nuimos'][mac_address].get('components', [])
                check_sonos_update(components)

            f.seek(0)  # We want to overwrite the config file with the new configuration
            f.truncate()
            yaml.dump(config, f, default_flow_style=False)

        with open(nuimo_app_config_path, 'r') as f:
            config = yaml.load(f)
            for mac_address in config['nuimos']:
                temp = config['nuimos'][mac_address]
                temp['mac_address'] = mac_address
                temp['battery_level'] = get_nuimo_battery_level(mac_address)
                nuimos.append(temp)

    except FileNotFoundError as e:
        logger.error(e)

#   [Alan] 'nuimo' in this context represents all the devices
#     controlled by a pyisical nuimo + the state of that nuimo.
#     Example with single nuimo:
#    (Epdb) nuimos
#    [{'mac_address': 'e0:88:72:c4:49:c2', 'name': 'My Nuimo', 'is_connected': True, 'components': [{'id': '69d965ea-1978-4db4-8b3e-0b63742ed31d', 'is_reachable': True, 'room_name': 'Devs 1', 'type': 'sonos', 'device_ids': ['7828ca17171e01400'], 'ip_address': '10.10.10.114', 'name': '10.10.10.114 - Sonos One'}], 'battery_level': 100}]

    return {'nuimos': nuimos}

prev_battery_level = {}


@check_for_update_service.get()
def get_update_service(request):  # pragma: no cover,
    nuimo_app_config_path = request.registry.settings['nuimo_app_config_path']
    is_updated = False
    with open(nuimo_app_config_path, 'r') as f:
        config = yaml.load(f)
    adapter_name = request.registry.settings.get('bluetooth_adapter_name', 'hci0')
    manager = ControllerManager(adapter_name=adapter_name)
    for mac_address in config['nuimos']:
        # check Nuimo connection Status
        controller = Controller(mac_address=mac_address, manager=manager)
        is_updated = True if config['nuimos'][mac_address]['is_connected'] != controller.is_connected() else is_updated
        if is_updated:
            return get_configured_nuimos(request)
        if controller.is_connected():
            global prev_battery_level
            prev_nuimo_battery_level = prev_battery_level.get(mac_address, None)
            is_updated = True if prev_nuimo_battery_level and prev_nuimo_battery_level != get_nuimo_battery_level(mac_address) else is_updated
            prev_battery_level[mac_address] = get_nuimo_battery_level(mac_address)
            if is_updated:
                return get_configured_nuimos(request)

        # check if New Sonos Groups have been created
        components = config['nuimos'][mac_address].get('components', [])
        is_updated = check_if_sonos_is_updated(components)
        if is_updated:
            return get_configured_nuimos(request)

    return {'is_updated': is_updated}


class ModifyNameSchema(MappingSchema):
    mac_address = SchemaNode(String())
    modified_name = SchemaNode(String(), validator=Length(min=1))


@configured_nuimos.put(schema=ModifyNameSchema, validators=(colander_body_validator,))
def modify_nuimo_name(request):  # pragma: no cover
    # TODO: Modify name of a particular nuimo
    mac_address = request.validated['mac_address'].replace('-', ':')
    mod_name = request.validated['modified_name']

    with open(request.registry.settings['nuimo_app_config_path'], 'r+') as f:
        config = yaml.load(f)

        try:
            target_nuimo = config['nuimos'][mac_address]
        except KeyError:
            return HTTPNotFound("No Nuimo with such ID")

        target_nuimo['name'] = mod_name

        f.seek(0)
        f.truncate()
        yaml.dump(config, f, default_flow_style=False)

    return {
        'mac_address': mac_address,
        'modified_name': mod_name,
        'message': 'SUCCESS'
    }


# TODO: add testcases
@nuimo_service.delete()
def delete_nuimo(request):  # pragma: no cover,
    mac_address = request.matchdict['mac_address'].replace('-', ':')
    with open(request.registry.settings['nuimo_app_config_path'], 'r+') as f:
        config = yaml.load(f)

        try:
            config['nuimos'][mac_address]
        except (KeyError, TypeError):
            return HTTPNotFound("No Nuimo with such ID")

        del config['nuimos'][mac_address]

        f.seek(0)  # We want to overwrite the config file with the new configuration
        f.truncate()
        yaml.dump(config, f, default_flow_style=False)

        try:
            if supervisor.program_status('nuimo_app') == 'RUNNING':
                supervisor.restart_program('nuimo_app')
        except Exception as e:
            # SUpervior spits out errors when two nuimos are being removed before the supervisor
            # restarts post first-nuimo-removal.
            logger.error(str(e))


# TODO: if required, due to performance issues, can be implemented in a separate endpoint
# TODO: add a timeout in order to handle bluetooth unexpected behaviour
def get_nuimo_battery_level(mac_address):  # pragma: no cover,
    try:
        fd = os.open('/tmp/' + mac_address.replace(':', '-'), os.O_RDONLY)
    except FileNotFoundError:
        logger.error("No memory mapped file named %s, return None battery level", mac_address.replace(':', '-'))
        return None
    buf = mmap.mmap(fd, mmap.PAGESIZE, mmap.MAP_SHARED, mmap.PROT_READ)
    result, = struct.unpack('i', buf[:4])
    return result


def check_sonos_update(components):  # pragma: no cover,
    master_component = None
    slave_components = []
    for component in components:
        if component['type'] == 'sonos':
            try:
                if is_device_responsive(component['ip_address']):
                    component['is_reachable'] = True
                    sonos = soco.SoCo(component['ip_address'])
                    component['room_name'] = sonos.player_name
                    join = component.get('join', None)
                    if len(component['device_ids']) != len(sonos.group.members) or join:
                        if len(sonos.group.members) > 1:
                            # JOIN from Sonos app
                            # TODO to be extended when just a speaker is removed from a group (e.g. group members decreased from 3 to 2)
                            if sonos.group.coordinator.ip_address == component['ip_address']:
                                component['join'] = {'master': True}
                                master_component = component
                            else:
                                component['join'] = {'master': False, 'ip_address': sonos.group.coordinator.ip_address}
                                slave_components.append(component)
                        elif join:
                            # UNJOIN from Sonos app
                            if join['master']:
                                for i, device in enumerate(component['device_ids']):
                                    for key, value in component['join'].items():
                                        if device == value:
                                            del component['device_ids'][i]
                            del component['join']
                else:
                    component['is_reachable'] = False
            except (requests.exceptions.RequestException, soco.SoCoException):
                logger.info("Sonos device non reachable %s", component['ip_address'])
                continue
    if master_component:
        for slave_component in slave_components:
            # TODO: extend to multiple groups handling
            if slave_component['device_ids'][0] not in master_component['device_ids']:
                master_component['device_ids'].extend(slave_component['device_ids'])
            master_component['join'][slave_component['ip_address']] = slave_component['device_ids'][0]


def check_if_sonos_is_updated(components):  # pragma: no cover,
    for component in components:
        if component['type'] == 'sonos':
            try:
                if is_device_responsive(component['ip_address']) != component['is_reachable']:
                    return True
                if is_device_responsive(component['ip_address']):
                    sonos = soco.SoCo(component['ip_address'])
                    if component['room_name'] != sonos.player_name:
                        return True
                    if len(component['device_ids']) != len(sonos.group.members):
                        return True
            except (requests.exceptions.RequestException, soco.SoCoException):
                logger.info("Sonos device non reachable %s", component['ip_address'])
                continue
    return False


def is_device_responsive(host_ip):  # pragma: no cover,
    param = "-c 1 -w 1"
    status = (system("ping " + param + " " + host_ip) == 0)
    return status
