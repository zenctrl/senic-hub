from os.path import exists

from cornice.service import Service
from pkg_resources import get_distribution

from ..config import path, get_logger


log = get_logger(__name__)


app_info = Service(
    name='appinfo',
    path=path(''),
    renderer='json',
    accept='application/json')


@app_info.get()
def get_app_info(request):
    return dict(
        version=get_distribution('senic_hub').version,
        onboarded=is_hub_onboarded(request)
    )


def is_hub_onboarded(request):
    nuimo_app_config_path = request.registry.settings['nuimo_app_config_path']
    devices_path = request.registry.settings['devices_path']
    homeassistant_config_path = request.registry.settings['homeassistant_config_path']
    nuimo_mac_address_filepath = request.registry.settings['nuimo_mac_address_filepath']

    return (exists(nuimo_app_config_path) and
            exists(devices_path) and
            exists(homeassistant_config_path) and
            exists(nuimo_mac_address_filepath))
