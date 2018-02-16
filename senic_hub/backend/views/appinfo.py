from cornice.service import Service
from ..config import path
from .api_descriptions import descriptions as desc
from .. import hub_metadata


app_info = Service(
    name='appinfo',
    path=path(''),
    description=desc.get('app_info'),
    renderer='json',
    accept='application/json')


@app_info.get()
def get_app_info(request):
    return dict(
        wifi=hub_metadata.HubMetaData.wifi(),
        os_version=hub_metadata.HubMetaData.os_version(),
        hardware_identifier=hub_metadata.HubMetaData.hardware_identifier(),
    )
