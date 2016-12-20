from json import loads
from pyramid.renderers import render
from pyramid.testing import DummyRequest
from pyramid.testing import setUp, tearDown
from pytest import fixture
from os import path
from webtest import TestApp as TestAppBase


def as_dict(content, **kw):
    return dict(loads(render('json', content, DummyRequest())), **kw)


@fixture
def route_url():

    def _route_url(name, **kwargs):
        return DummyRequest().route_url(name, **kwargs)

    return _route_url


def asset_path(*parts):
    return path.abspath(path.join(path.dirname(__file__), 'data', *parts))


# settings for test configuration
settings = {
    'testing': True,
    'debug': False,
}


@fixture
def config(request):
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
    from senic.nuimo_hub import views
    return views


@fixture
def app(config):
    """ Returns WSGI application wrapped in WebTest's testing interface. """
    from .config import configure
    return configure({}, **config.registry.settings).make_wsgi_app()


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
