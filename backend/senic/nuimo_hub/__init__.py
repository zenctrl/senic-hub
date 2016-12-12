def main(global_config, **settings):        # pragma: no cover, tests have own app setup
    from .config import configure
    config = configure(global_config, **settings)
    return config.make_wsgi_app()
