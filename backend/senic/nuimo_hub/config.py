# -*- coding: utf-8 -*-
import logging
from pyramid.config import Configurator


def get_logger(name):
    return logging.getLogger('senic.nuimo_hub.%s' % name)


project_name = 'nuimo_hub'
log = get_logger(__name__)


def path(service):
    """ Return path — or route pattern — for the given REST service. """
    return '/-/{0}'.format(service.lower())


def configure(global_config, **settings):
    config = Configurator(settings=settings)
    config.begin()
    scan_ignore = ['.tests', '.testing']
    config.include('cornice')
    config.scan(ignore=scan_ignore)
    config.commit()
    return config
