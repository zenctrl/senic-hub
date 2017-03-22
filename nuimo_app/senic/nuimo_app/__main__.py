import configparser
import logging
import sys

from . import components, errors

from .hass import HAListener
from .nuimo_app import NuimoApp


DEFAULT_BLE_ADAPTER_NAME = "hci0"
DEFAULT_CONFIG_FILE_PATH = "/srv/nuimo_app/data/nuimo_app.cfg"
DEFAULT_LOGGING_LEVEL = "WARNING"


logger = logging.getLogger(__name__)


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

    ha_url = config.get("ha_api_url", "localhost:8123")
    ha_api = HAListener("ws://{}".format(ha_url))
    ha_api.start()

    ble_adapter_name = config.get("ble_adapter_name", DEFAULT_BLE_ADAPTER_NAME)
    nuimo_app = NuimoApp(ha_api, ble_adapter_name, controller_mac_address)

    for cid in component_config.sections():
        cfg = component_config[cid]
        component_class = getattr(components, cfg["component"])
        component = component_class(cfg["name"], cfg["entity_id"])
        nuimo_app.register_component(component)

    try:
        nuimo_app.run()
    except (KeyboardInterrupt, errors.NuimoControllerConnectionError):
        logger.debug("Stopping...")
        ha_api.stop()
        nuimo_app.stop()


def read_config(config_file_path):
    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config["DEFAULT"], config


if __name__ == "__main__":
    main()
