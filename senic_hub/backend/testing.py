from contextlib import contextmanager
from json import loads
from os import path, remove
from tempfile import NamedTemporaryFile

from pyramid.renderers import render
from pyramid.testing import DummyRequest


def asset_path(*parts):
    return path.abspath(path.join(path.dirname(__file__), 'tests', 'data', *parts))


@contextmanager
def temp_asset_path(name, *parts):
    with NamedTemporaryFile('w+', delete=False) as f:
        temp_file_name = f.name
        with open(asset_path(name, *parts)) as config_file:
            f.write(config_file.read())
    yield temp_file_name
    remove(temp_file_name)


def as_dict(content, **kw):
    return dict(loads(render('json', content, DummyRequest())), **kw)
