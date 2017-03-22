from cornice.service import Service
from logging import getLogger
from os import path
from .. import nuimo_setup
# TODO: We better rename `config.path` to something else. Conflicts with `os.path`
from ..config import path as service_path


logger = getLogger(__name__)


nuimo_bootstrap = Service(
    name='start_nuimo_setup',
    path=service_path('setup/nuimo/bootstrap'),
    renderer='json',
    accept='application/json')


connected_nuimos = Service(
    name='connected_nuimos',
    path=service_path('setup/nuimo'),
    renderer='json',
    accept='application/json')


# TODO: Remove get()
@nuimo_bootstrap.get()
@nuimo_bootstrap.post()
def bootstrap_nuimos(request):  # pragma: no cover,
    adapter_name = request.registry.settings.get('bluetooth_adapter_name', 'hci0')
    required_mac_address = request.registry.settings.get('nuimo_mac_address')
    setup = nuimo_setup.NuimoSetup(adapter_name=adapter_name)
    mac_address = setup.discover_and_connect_controller(required_mac_address=required_mac_address, timeout=60)
    logger.debug("Discovered and connected Nuimo: %s", mac_address)
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
        return {'connectedControllers': []}
    with open(nuimo_mac_address_filepath, 'r') as nuimo_mac_address_file:
        mac_address = nuimo_mac_address_file.readline().strip()
        return {'connectedControllers': [mac_address]}
