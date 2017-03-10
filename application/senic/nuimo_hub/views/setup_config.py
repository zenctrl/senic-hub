from cornice.service import Service

from ..commands import create_configuration_files_and_restart_apps_
from ..config import path


configuration_service = Service(
    name='configuration_create',
    path=path('setup/config'),
    renderer='json',
    accept='application/json',
)


@configuration_service.post()
def configuration_create_view(request):
    create_configuration_files_and_restart_apps_(request.registry.settings)
    return {}
