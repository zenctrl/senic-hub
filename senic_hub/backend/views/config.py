from time import sleep

from cornice.service import Service

from ..commands import create_configuration_files_and_restart_apps
from ..config import path
from ..supervisor import stop_program
import subprocess


configuration_service = Service(
    name='configuration',
    path=path('config'),
    renderer='json',
    accept='application/json',
)


@configuration_service.post()
def configuration_view(request):
    stop_program('device_discovery')

    create_configuration_files_and_restart_apps(request.registry.settings)

    # Wait for Nuimo App to restart and connect to Nuimo
    # TODO: Add D-Bus interface to Nuimo and wait for its ready signal
    sleep(10.0)

@configuration_service.delete()
def configuration_view(request):
    subprocess.Popen(['/usr/bin/senic_hub_factory_reset'])
