# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from pyramid.config import Configurator
from pyramid.renderers import JSON
from transaction import commit

from .models import db_session, metadata, Root
from .utils import create_db_engine, get_logger


# project/package name
project_name = 'nuimo_hub'
log = get_logger(__name__)

# prepare for translation factory
_ = lambda string: string


def path(service):
    """ Return path — or route pattern — for the given REST service. """
    return '/-/{0}'.format(service.lower())


def datetime_adapter(obj, request):
    if obj is not None:
        return obj.isoformat()


def str_adapter(obj, request):
    if obj is not None:
        return str(obj)


json_renderer = JSON()
json_renderer.add_adapter(datetime, datetime_adapter)
json_renderer.add_adapter(timedelta, str_adapter)


def configure(global_config, **settings):
    config = Configurator(settings=settings)
    config.begin()
    scan_ignore = ['.tests', '.testing']

    config.set_root_factory(lambda request: Root())
    config.add_renderer('json', json_renderer)
    config.include('cornice')
    config.scan(ignore=scan_ignore)
    config.commit()
    return config


def db_setup(**settings):
    engine = create_db_engine(**settings)
    db_session.registry.clear()
    db_session.configure(bind=engine)
    metadata.bind = engine


def main(global_config, **settings):        # pragma: no cover, tests have own app setup
    config = configure(global_config, **settings)
    db_setup(**settings)
    commit()
    return config.make_wsgi_app()
