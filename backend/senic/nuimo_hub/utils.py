from os import environ
from sqlalchemy import engine_from_config
import logging


def get_logger(name):
    return logging.getLogger('senic.nuimo_hub.%s' % name)


log = get_logger(__name__)


def create_db_engine(prefix='sqlalchemy.', suffix='', project_name=None, **settings):
    key = prefix + 'url'
    url = 'postgresql:///%%s%s' % suffix
    if 'PGDATABASE' in environ:
        settings[key] = url % environ['PGDATABASE']
    elif key not in settings:
        settings[key] = url % project_name
    settings.setdefault(prefix + 'echo', bool(environ.get('SQLALCHEMY_ECHO')))
    return engine_from_config(settings, prefix=prefix)
