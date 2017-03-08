import sys
from os import path


def main(global_config, **settings):        # pragma: no cover, tests have own app setup
    settings['bin_path'] = path.dirname(sys.executable)
    from .config import configure
    settings['fs_config_ini'] = global_config['__file__']
    config = configure(global_config, **settings)
    return config.make_wsgi_app()
