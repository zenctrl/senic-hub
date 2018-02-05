from pyramid.testing import DummyRequest
from pyramid.testing import setUp, tearDown
from pytest import fixture
from webtest import TestApp as TestAppBase

from senic_hub.backend.testing import asset_path


@fixture
def route_url(app):

    def _route_url(name, **kwargs):
        return DummyRequest().route_url(name, **kwargs)

    return _route_url


# settings for test configuration
@fixture
def settings():
    return {
        'testing': True,
        'debug': False,
        'bin_path': asset_path('bin'),
        'wifi_networks_path': asset_path('wifi_networks.json'),
        'wifi_setup_flag_path': asset_path('nuimo_setup_required'),
        'wifi_adhoc_ssid': 'Setup Nuimo',
        'crypto_settings_datafile': asset_path('testing.yml.aes'),
        'crypto_settings_keyfile': asset_path('testing.key'),
        'devices_path': asset_path('devices.json'),
        'data_path': '/tmp',
        'nuimo_mac_address_filepath': asset_path('nuimo_mac_address.txt'),
        'nuimo_app_config_path': asset_path('nuimo_app.yaml'),
        'config_ini_path': '/no/such/file.ini',
        'joined_wifi_path': asset_path('joined_wifi.json'),
        'senic_hub_data_path': asset_path(),
        'hub_ip_address': '0.0.0.0'
    }


@fixture
def config(request, settings):
    """ Sets up a Pyramid `Configurator` instance suitable for testing. """
    config = setUp(settings=dict(settings))
    request.addfinalizer(tearDown)
    return config


class TestApp(TestAppBase):

    def get_json(self, url, params=None, headers=None, *args, **kw):
        if headers is None:
            headers = {}
        headers['Accept'] = 'application/json'
        return self.get(url, params, headers, *args, **kw)


@fixture(scope='session')
def testing():
    """ Returns the `testing` module. """
    from sys import modules
    return modules[__name__]    # `testing.py` has already been imported


@fixture(scope='session')
def views():
    """ Returns the `views` module. """
    from senic_hub.backend import views
    return views


@fixture
def app(config):
    """ Returns WSGI application wrapped in WebTest's testing interface. """
    from senic_hub.backend.config import configure
    return configure({'__file__': 'testing.ini'}, **config.registry.settings).make_wsgi_app()


@fixture
def dummy_request(request, config):
    config.manager.get()['request'] = req = DummyRequest()
    return req


@fixture
def browser(app, request):
    """ Returns an instance of `webtest.TestApp`.  The `user` pytest marker
        (`pytest.mark.user`) can be used to pre-authenticate the browser
        with the given login name: `@user('admin')`. """
    extra_environ = dict(HTTP_HOST='example.com')
    browser = TestApp(app, extra_environ=extra_environ)
    return browser


@fixture
def dummy_url(browser):
    """ a url we can render during tests (points to a dummy page)"""
    return route_url('dummy_target')


@fixture
def philips_hue_bridge_description():
    return """
        <root xmlns="urn:schemas-upnp-org:device-1-0">
          <device>
            <friendlyName>Philips Hue bridge</friendlyName>
            <serialNumber>ph1</serialNumber>
          </device>
        </root>"""


@fixture
def sonos_speaker_description():
    return """
        <root xmlns="urn:schemas-upnp-org:device-1-0">
          <device>
            <friendlyName>192.168.1.42 Foo Bar</friendlyName>
            <UDN>uuid:RINCON_123</UDN>
            <roomName>Foo Bar</roomName>
          </device>
        </root>"""
