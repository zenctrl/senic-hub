import logging
import nuimo
import gatt
import threading


logger = logging.getLogger(__name__)


class NuimoSetup(nuimo.ControllerManagerListener, nuimo.ControllerListener):  # pragma: no cover

    def __init__(self, adapter_name):
        self._gatt_manager = gatt.DeviceManager(adapter_name)
        self._manager = nuimo.ControllerManager(adapter_name)
        self._manager.listener = self
        self._is_running = False  # Prevents from considering D-Bus events if we aren't running
        self._discovery_timeout_timer = None
        self._connect_timeout_timer = None
        self._controller = None
        self._required_mac_address = None

    def discover_and_connect_controller(self, required_mac_address=None, timeout=None):
        """
        Discovers and connects to a Nuimo controller.

        :param required_mac_address: Connects only to this Nuimo, if specified
        :param timeout: Timeout in seconds after which we stop the discovery
        :return: MAC address of connected Nuimo controller or `None` if none connected
        """
        logger.info("Discover and connect Nuimo controller with timeout = %f", timeout)
        self._gatt_manager.remove_all_devices(skip_alias='Nuimo')

        self._manager.is_adapter_powered = True
        # If there's already a connected Nuimo, take it and don't run discovery
        for controller in self._manager.controllers():
            if controller.is_connected():
                logger.info("Already connected controller %s, looking for another one", controller.mac_address)
        # Start discovery
        self._required_mac_address = required_mac_address
        self._is_running = True
        if timeout:
            self._discovery_timeout_timer = threading.Timer(timeout, self.discovery_timed_out)
            self._discovery_timeout_timer.start()
        self._controller = None
        self._manager.start_discovery()
        # Start D-Bus event loop. This call is blocking until the loop gets stopped.
        # Will be stopped when a controller was connected (see below).
        self._manager.run()
        self._is_running = False
        logger.debug("Stopped")
        if self._discovery_timeout_timer:
            self._discovery_timeout_timer.cancel()
        if self._connect_timeout_timer:
            self._connect_timeout_timer.cancel()
        if self._controller and self._controller.is_connected():
            return self._controller.mac_address
        else:
            return None

    def _restart_discovery(self):
        if not self._is_running:
            return
        logger.debug("restarting discovery")
        self._manager.start_discovery()

    def discovery_timed_out(self):
        if not self._is_running:
            return
        logger.debug("Discovery timed out, stopping now")
        self._is_running = False
        if self._connect_timeout_timer:
            self._connect_timeout_timer.cancel()
        if self._controller:
            self._controller.disconnect()
        self._manager.stop_discovery()
        self._manager.stop()

    def controller_discovered(self, controller):
        if not self._is_running:
            return
        if self._controller is not None:
            logger.debug("%s discovered but ignored, already connecting to another one", controller.mac_address)
            return
        if self._required_mac_address and (self._required_mac_address.lower() != controller.mac_address.lower()):
            logger.debug("%s discovered but ignored because we look for a specific one", controller.mac_address)
            return
        logger.debug("%s discovered, stopping discovery and trying to connect", controller.mac_address)
        self._manager.stop_discovery()
        self._connect_timeout_timer = threading.Timer(20, self.connect_timed_out)
        self._connect_timeout_timer.start()
        self._controller = controller
        self._controller.listener = self
        self._controller.connect()

    def connect_succeeded(self):
        if not self._is_running:
            return
        logger.debug("%s successfully connected, stopping now", self._controller.mac_address)
        if self._connect_timeout_timer:
            self._connect_timeout_timer.cancel()
        self._manager.stop()

    def connect_failed(self, error):
        if not self._is_running:
            return
        logger.info("%s connection failed: %s", self._controller.mac_address, error)
        self._manager.stop_discovery()
        self._connect_timeout_timer = threading.Timer(20, self.connect_timed_out)
        self._connect_timeout_timer.start()
        self._controller.listener = self
        self._controller.connect()

    def connect_timed_out(self):
        if not self._is_running:
            return
        self.connect_failed(Exception("Timeout"))
