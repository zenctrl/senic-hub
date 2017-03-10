import sys
from os import path
from .config import configure


def main(global_config, **settings):        # pragma: no cover, tests have own app setup
    settings['bin_path'] = path.dirname(sys.executable)
    config = configure(global_config, **settings)
    return config.make_wsgi_app()
