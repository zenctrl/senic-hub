from cornice_swagger import CorniceSwagger
from cornice.service import get_services, Service
from logging import getLogger

from ..config import path as service_path
from .api_descriptions import descriptions as desc

logger = getLogger(__name__)

api_json_generator = Service(
    name='api_json_genrator',
    path=service_path('api_json'),
    description=desc.get('api_json_generator'),
    renderer='json',
    accept='application/json',
)


@api_json_generator.get()
def generate_json(request):  # pragma: no cover

    serv_json = CorniceSwagger(get_services())
    spec = serv_json.generate('Senic Hub API', request.registry.settings.get('hub_api_version'))
    return spec
