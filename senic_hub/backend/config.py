# -*- coding: utf-8 -*-
import logging
from pyramid.config import Configurator


def get_logger(name):
    return logging.getLogger('senic_hub.backend.%s' % name)


project_name = 'nuimo_hub'
log = get_logger(__name__)


default_settings = dict(
    wifi_networks_path='/tmp/wifi_networks.json',
    wifi_setup_flag_path='/srv/nuimo_hub/data/WIFI_SETUP_REQUIRED',
    hass_phue_config_path='/srv/nuimo_hass/data/phue.conf',
)


def path(service):
    """ Return path — or route pattern — for the given REST service. """
    return '/-/{0}'.format(service.lower())


def configure(global_config, **settings):
    config = Configurator(settings=dict(default_settings, **settings))
    config.begin()
    scan_ignore = ['.tests', '.testing']
    config.include('cornice')
    config.scan(ignore=scan_ignore)
    config.registry.crypto_settings = crypto_settings(global_config, **settings)
    config.commit()
    return config


def crypto_settings(global_config, **settings):
    """reads the encrypted settings from the filesytem and returns them
    as a `senic.cryptoyaml.CryptoYAML` instance.
    It looks for `crypto_settings_datafile` and `crypto_settings_keyfile` in the
    settings to initialize it but defaults to `XXX.yml.aes` and `XXX.key` respectively
    where XXX is the basename of the ini file used.

    I.e. if the inifile being read is `development.ini` and there exist next to it two files
    `development.key` and `developmen.yml.aes` then those will be used by default.
    """
    from os import path
    from cryptoyaml import CryptoYAML, generate_key
    basename = path.splitext(path.basename(global_config['__file__']))[0]
    settings_datafile = '{}.yml.aes'.format(basename)
    settings_datafile = settings.get('crypto_settings_datafile', settings_datafile)
    settings_keyfile = '{}.key'.format(basename)
    settings_keyfile = settings.get('crypto_settings_keyfile', settings_keyfile)
    if not path.exists(settings_keyfile):
        generate_key(settings_keyfile)
    return CryptoYAML(settings_datafile, keyfile=settings_keyfile)
