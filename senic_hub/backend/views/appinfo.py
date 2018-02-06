from cornice.service import Service
from ..config import path, get_logger
from .api_descriptions import descriptions as desc

import re
import os.path

log = get_logger(__name__)


app_info = Service(
    name='appinfo',
    path=path(''),
    description=desc.get('app_info'),
    renderer='json',
    accept='application/json')


@app_info.get()
def get_app_info(request):
    return dict(
        wifi=wifi(),
        os_version=os_version(),
        hardware_identifier=hardware_identifier(),
    )


def wifi():  # pragma: no cover
    bluenet = '/etc/NetworkManager/system-connections/bluenet'

    if not os.path.isfile(bluenet):
        return ''

    for line in open(bluenet):
        if 'ssid=' in line:
            ssid = re.split('ssid=', line)[1].strip()
            return ssid

    return ''


def os_version():  # pragma: no cover
    osrelease = '/etc/os-release'

    if not os.path.isfile(osrelease):
        return ''

    for line in open(osrelease):
        if 'VERSION=' in line:
            version = re.split('VERSION=', line)[1].strip().replace('"', '')
            return version

    return ''


def hardware_identifier():  # pragma: no cover
    cpuinfo = '/proc/cpuinfo'

    if not os.path.isfile(cpuinfo):
        return ''

    for line in open(cpuinfo):
        if 'Serial' in line:
            serial = re.split(':\s*', line)[1].strip().replace('02c00081', '')
            return serial

    return ''
