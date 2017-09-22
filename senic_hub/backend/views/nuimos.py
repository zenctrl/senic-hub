from cornice.service import Service
from logging import getLogger
from os import path
from .. import nuimo_setup
# TODO: We better rename `config.path` to something else. Conflicts with `os.path`
from ..config import path as service_path
from pyramid.httpexceptions import HTTPNotFound
import yaml
from .. import supervisor

import soco
import gatt
import binascii
from nuimo import Controller, ControllerManager

logger = getLogger(__name__)


connected_nuimos = Service(
    name='connected_nuimos',
    path=service_path('nuimos'),
    renderer='json',
    accept='application/json')


configured_nuimos = Service(
    name='configured_nuimos',
    path=service_path('confnuimos'),
    renderer='json',
    accept='application/json')


nuimo_service = Service(
    name='nuimo_services',
    path=service_path('nuimos/{mac_address:[a-z0-9\-]+}'),
    renderer='json',
    accept='application/json',
)


@connected_nuimos.post()
def bootstrap_nuimos(request):  # pragma: no cover,
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

    with open(nuimo_app_config_path, 'r+') as f:
        config = yaml.load(f)
        adapter_name = request.registry.settings.get('bluetooth_adapter_name', 'hci0')
        manager = ControllerManager(adapter_name=adapter_name)
        for mac_address in config['nuimos']:
            # check Nuimo connection Status
            controller = Controller(mac_address=mac_address, manager=manager)
            config['nuimos'][mac_address]['is_connected'] = controller.is_connected()
            if config['nuimos'][mac_address]['is_connected']:
                config['nuimos'][mac_address]['battery_level'] = get_nuimo_battery_level(mac_address, manager)

            # check if New Sonos Groups have been created
            components = config['nuimos'][mac_address].get('components', [])
            master_component = None
            slave_components = []
            for component in components:
                if component['type'] == 'sonos':
                    try:
                        sonos = soco.SoCo(component['ip_address'])
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
                    except soco.SoCoException:
                        continue
            if master_component:
                for slave_component in slave_components:
                    # TODO: extend to multiple groups handling
                    if slave_component['device_ids'][0] not in master_component['device_ids']:
                        master_component['device_ids'].extend(slave_component['device_ids'])
                    master_component['join'][slave_component['ip_address']] = slave_component['device_ids'][0]

        f.seek(0)  # We want to overwrite the config file with the new configuration
        f.truncate()
        yaml.dump(config, f, default_flow_style=False)

    with open(nuimo_app_config_path, 'r') as f:
        config = yaml.load(f)
        for mac_address in config['nuimos']:
            temp = config['nuimos'][mac_address]
            temp['mac_address'] = mac_address
            nuimos.append(temp)

    return {'nuimos': nuimos}


# TODO: add testcases
@nuimo_service.delete()
def delete_nuimo(request):  # pragma: no cover,
    mac_address = request.matchdict['mac_address'].replace('-', ':')
    with open(request.registry.settings['nuimo_app_config_path'], 'r+') as f:
        config = yaml.load(f)

        try:
            config['nuimos'][mac_address]
        except KeyError:
            return HTTPNotFound("No Nuimo with such ID")

        del config['nuimos'][mac_address]

        f.seek(0)  # We want to overwrite the config file with the new configuration
        f.truncate()
        yaml.dump(config, f, default_flow_style=False)

        supervisor.restart_program('nuimo_app')


# TODO: if required, due to performance issues, can be implemented in a separate endpoint
# TODO: add a timeout in order to handle bluetooth unexpected behaviour
def get_nuimo_battery_level(mac_address, manager):  # pragma: no cover,

    class AnyDevice(gatt.Device):
        battery_level = None

        def services_resolved(self):
            super().services_resolved()

            device_information_service = next(
                s for s in self.services
                if s.uuid == '0000180f-0000-1000-8000-00805f9b34fb')

            firmware_version_characteristic = next(
                c for c in device_information_service.characteristics
                if c.uuid == '00002a19-0000-1000-8000-00805f9b34fb')

            firmware_version_characteristic.read_value()

        def characteristic_value_updated(self, characteristic, value):
            hexvalue = binascii.hexlify(value)
            self.battery_level = int(hexvalue, 16)
            logger.info("Battery Level: %d ", self.battery_level)
            manager.stop()

    device = AnyDevice(mac_address=mac_address, manager=manager)
    device.connect()

    manager.run()
    return device.battery_level
