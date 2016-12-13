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
    result = dict(
        version=get_distribution('senic.nuimo_hub').version,
    )
    return result
