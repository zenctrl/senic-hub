import configparser
import logging
import sys

from importlib import import_module

from . import NuimoApp


# TODO: Read from main ini file
DEFAULT_BLE_ADAPTER_NAME = "hci0"
# TODO: Read path to `nuimo_app.cfg` from main ini file
DEFAULT_CONFIG_FILE_PATH = "/srv/senic_hub/data/nuimo_app.cfg"
# TODO: Read value from main ini file
DEFAULT_LOGGING_LEVEL = "WARNING"


logger = logging.getLogger(__name__)


# TODO: Remove default argument so this app needs to be called with a path to an ini file
def main(config_file_path=DEFAULT_CONFIG_FILE_PATH):
    if len(sys.argv) > 1:
        config_file_path = sys.argv[-1]

    config, component_config = read_config(config_file_path)

    log_level = getattr(logging, config.get("logging_level", DEFAULT_LOGGING_LEVEL), DEFAULT_LOGGING_LEVEL)
    log_format = "%(asctime)s %(levelname)s %(name)s %(message)s"
    logging.basicConfig(level=log_level, format=log_format)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)

    logger.info("Using configuration from: %s", config_file_path)

    controller_mac_address = config.get("controller_mac_address")
    if not controller_mac_address:
        logger.error("Nuimo controller MAC address not configured")
        sys.exit(1)

    ha_api_url = config.get("ha_api_url", "localhost:8123")
    ble_adapter_name = config.get("ble_adapter_name", DEFAULT_BLE_ADAPTER_NAME)
    component_instances = get_component_instances(component_config)
    nuimo_app = NuimoApp(ha_api_url, ble_adapter_name, controller_mac_address, component_instances)

    try:
        nuimo_app.start()
    except KeyboardInterrupt:
        logger.debug("Stopping...")
        nuimo_app.stop()


def read_config(config_file_path):
    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config["DEFAULT"], config


def get_component_instances(component_config):
    """
    Import component modules configured in the Nuimo app configuration
    and return instances of the contained component classes.
    """
    instances = []

    module_name_format = __name__.rsplit('.', 1)[0] + '.components.{}'

    for cid in component_config.sections():
        cfg = component_config[cid]
        module_name = module_name_format.format(cfg.pop('component'))
        logger.info("Importing module %s", module_name)
        component_module = import_module(module_name)
        instances.append(component_module.Component(cfg))

    return instances


if __name__ == "__main__":
    main()
