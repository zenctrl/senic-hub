import json

from unittest import mock

from senic_hub.backend.testing import asset_path, temp_asset_path
from senic_hub.backend import hub_metadata


def test_read_from_file_fail():
    assert hub_metadata.HubMetaData._read_from_file('os_info') == ''


def test_read_from_file_success():
    with temp_asset_path('os-release') as os_info:
        assert hub_metadata.HubMetaData._read_from_file(os_info) == [
            'ID="senic-dev"\n',
            'NAME="senic"\n',
            'VERSION="0.1.8"\n',
            'VERSION_ID="0.1.8"\n',
            'PRETTY_NAME="senic 0.1.8"\n',
            'BUILD_DATE="Fri Jan 26 11:27:38 CET 2018"\n',
            'meta=2017-10-206-g68a3f33027\n',
            'meta-senic=0.1.8\n',
            'meta-oe=6e3fc5b8d\n',
            'meta-networking=6e3fc5b8d\n',
            'meta-python=6e3fc5b8d\n',
            'meta-mender-core=rocko-v2018.01-28-g18dfa93'
        ]


def test_read_from_json_file():
    devices = hub_metadata.HubMetaData._read_from_file(
        asset_path('devices.json')
    )
    assert devices == [
        {
            'id': 'ph1',
            'type': 'philips_hue',
            'name': 'Philips Hue Bridge 1',
            'ip': '127.0.0.1',
            'authenticationRequired': True,
            'authenticated': False,
            'extra': {}
        },
        {
            'id': 'ph2',
            'type': 'philips_hue',
            'name': 'Philips Hue Bridge 2',
            'ip': '127.0.0.2',
            'authenticationRequired': True,
            'authenticated': True,
            'extra': {
                'username': 'light_bringer',
                'lights': {
                    '5': {'name': ' Light 5'},
                    '7': {'name': ' Light 7'},
                    '4': {'name': ' Light 4'},
                    '8': {'name': ' Light 8'},
                    '6': {'name': ' Light 6'}
                },
                'bridge': {
                    'apiversion': '1.22.0',
                    'datastoreversion': '65',
                    'mac': '00:17:88:79:53:98',
                    'swversion': '1711151408'
                }
            }
        },
        {
            'id': 's1',
            'type': 'sonos',
            'name': 'Sonos Player S1',
            'ip': '127.0.0.1',
            'authenticationRequired': False,
            'authenticated': True,
            'extra': {}
        }
    ]


@mock.patch('senic_hub.backend.hub_metadata.HubMetaData._read_from_file')
def test_os_version_success(mocked_function):
    with open(asset_path('os-release')) as f:
        mocked_function.return_value = f.readlines()
        assert hub_metadata.HubMetaData.os_version() == '0.1.8'


@mock.patch('senic_hub.backend.hub_metadata.HubMetaData._read_from_file')
def test_os_version_fail(mocked_function):
    with open(asset_path('empty')) as f:
        mocked_function.return_value = f.readlines()
        assert hub_metadata.HubMetaData.os_version() == ''


@mock.patch('senic_hub.backend.hub_metadata.HubMetaData._read_from_file')
def test_wifi_success(mocked_function):
    with open(asset_path('system-connections')) as f:
        mocked_function.return_value = f.readlines()
        assert hub_metadata.HubMetaData.wifi() == 'test'


@mock.patch('senic_hub.backend.hub_metadata.HubMetaData._read_from_file')
def test_wifi_fail(mocked_function):
    with open(asset_path('empty')) as f:
        mocked_function.return_value = f.readlines()
        assert hub_metadata.HubMetaData.wifi() == ''


@mock.patch('senic_hub.backend.hub_metadata.HubMetaData._read_from_file')
def test_hardware_identifier_success(mocked_function):
    with open(asset_path('cpuinfo')) as f:
        mocked_function.return_value = f.readlines()
        assert hub_metadata.HubMetaData.hardware_identifier() == '9e32509e'


@mock.patch('senic_hub.backend.hub_metadata.HubMetaData._read_from_file')
def test_hardware_identifier_fail(mocked_function):
    with open(asset_path('empty')) as f:
        mocked_function.return_value = f.readlines()
        assert hub_metadata.HubMetaData.hardware_identifier() == ''


@mock.patch('senic_hub.backend.hub_metadata.HubMetaData._read_from_file')
def test_phue_bridge_info_success(mocked_function):
    with open(asset_path('devices.json')) as f:
        mocked_function.return_value = json.load(f)
        assert hub_metadata.HubMetaData.phue_bridge_info('', '127.0.0.2') == {
            'apiversion': '1.22.0',
            'datastoreversion': '65',
            'mac': '00:17:88:79:53:98',
            'swversion': '1711151408'
        }


@mock.patch('senic_hub.backend.hub_metadata.HubMetaData._read_from_file')
def test_phue_bridge_info_missing_extra_info(mocked_function):
    with open(asset_path('devices.json')) as f:
        mocked_function.return_value = json.load(f)
        assert hub_metadata.HubMetaData.phue_bridge_info('', '127.0.0.1') == {}


@mock.patch('senic_hub.backend.hub_metadata.HubMetaData._read_from_file')
def test_phue_bridge_info_wrong_ip(mocked_function):
    with open(asset_path('devices.json')) as f:
        mocked_function.return_value = json.load(f)
        assert hub_metadata.HubMetaData.phue_bridge_info('', '127.0.0.5') == {}
