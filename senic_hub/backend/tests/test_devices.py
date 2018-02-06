from pytest import fixture


@fixture
def url(route_url):
    return route_url('devices')


@fixture
def no_devices_file(settings):
    settings['devices_path'] = '/no/such/file'
    return settings


def test_devices_returns_empty_list_if_devices_file_doesnt_exist(no_devices_file, url, browser):
    assert browser.get_json(url, status=200).json == {'devices': []}


def test_devices_returns_all_devices(url, browser):
    assert browser.get_json(url, status=200).json == {'devices': [
        {
            "id": "ph1",
            "type": "philips_hue",
            "name": "Philips Hue Bridge 1",
            "ip": "127.0.0.1",
            "virtual": True,
            "authenticationRequired": True,
            "authenticated": False,
        },
        {
            "id": "ph2",
            "type": "philips_hue",
            "name": "Philips Hue Bridge 2",
            "ip": "127.0.0.2",
            "virtual": True,
            "authenticationRequired": True,
            "authenticated": True,
        },
        {
            "id": "ph2-light-4",
            "type": "philips_hue",
            "name": " Light 4",
        },
        {
            "id": "ph2-light-5",
            "type": "philips_hue",
            "name": " Light 5",
        },
        {
            "id": "ph2-light-6",
            "type": "philips_hue",
            "name": " Light 6",
        },
        {
            "id": "ph2-light-7",
            "type": "philips_hue",
            "name": " Light 7",
        },
        {
            "id": "ph2-light-8",
            "type": "philips_hue",
            "name": " Light 8",
        },
        {
            "id": "s1",
            "type": "sonos",
            "name": "Sonos Player S1",
            "ip": "127.0.0.1",
            "authenticationRequired": False,
            "authenticated": True,
        },
    ]}
