import logging
import nuimo
import gatt
import threading
import time
import subprocess

logger = logging.getLogger(__name__)

# If any of these timeouts are reached,
# both BlueZ and the bluetooth module
# (via the reset pin) are reset
# and the proces is retried
DISCOVERY_TIMEOUT = 5
CONNECTION_TIMEOUT = 10

# Onboarding in the context of this file means
# a succefull discovery and connecion to a nuimo
MAX_ONBOARDING_ATTEMPTS = 3


class NuimoSetup(nuimo.ControllerManagerListener, nuimo.ControllerListener):  # pragma: no cover

    def __init__(self, adapter_name):
        self._adapter_name = adapter_name
        self._gatt_manager = gatt.DeviceManager(self._adapter_name)
        self._manager = nuimo.ControllerManager(self._adapter_name)
        self._manager.listener = self
        self._is_running = False  # Prevents from considering D-Bus events if we aren't running
        self._discovery_timeout_timer = None
        self._connect_timeout_timer = None
        self._controller = None
        self._required_mac_address = None
        self._discovery_duration = None
        self._connect_duration = None
        self._nuimo_connected = False
        self._nuimo_onboarding_attempts = 0

        # A control flag not to do any action while restart
        # is underway
        self._bt_restart_underway = False

    def _restart_bluetooth(self):
        """
        Restarts BlueZ and hard resets the BT module.

        Sets the self._bt_restart_underway to false
        to signal the end of bt restart.

        It also reinitialises the python objects of this class
        responsible for interacting with the underlying bt infrastructure.
        """

        hard_reset_module_cmd = "systemctl restart enable-bt-module"
        restart_bluez_cmd = "systemctl restart bluetooth"

        logger.debug("Hard restarting systemd bluetooth related services")
        subprocess.run(hard_reset_module_cmd.split())
        subprocess.run(restart_bluez_cmd.split())

        # Reinitialise the depend on the bt module
        # Assumed this is needed, not confirmed
        logger.debug("Reinitialisng python object after restart")
        del self._gatt_manager
        del self._manager
        self._gatt_manager = gatt.DeviceManager(self._adapter_name)
        self._manager = nuimo.ControllerManager(self._adapter_name)

        # This smells like it could cause trouble.
        # Do doubt it for it wasn't thought of deeply.
        del self._manager.listener
        self._manager.listener = self
        self._controller = None

        logger.debug("Powering BT module after restart")
        self._manager.is_adapter_powered = True
        self._bt_restart_underway = False
        logger.info("Bluetooth restart done")

    def discover_and_connect_controller(self, required_mac_address=None, timeout=None):
        """
        Discovers and connects to a Nuimo controller.

        :param required_mac_address: Connects only to this Nuimo, if specified
        :param timeout: Timeout in seconds after which we stop the discovery
        :return: MAC address of connected Nuimo controller or `None` if none connected
        """

        # Inherited, didn't question it.
        # This is the only part where gatt is used directly
        # for all other bt operations nuimo.ControllerManager is used
        self._gatt_manager.remove_all_devices(skip_alias='Nuimo')

        # Same thing as:
        #    echo "power on" | bluetoothctl
        self._manager.is_adapter_powered = True

        # This is the main loop for establishing a connection a new nuimo.
        while True:
            self._nuimo_onboarding_attempts += 1
            self._start_onboarding()
            if self._nuimo_connected:
                break
            if self._nuimo_onboarding_attempts == MAX_ONBOARDING_ATTEMPTS:
                break
            while self._bt_restart_underway:
                logger.debug("Bluetooth restart underway... waiting")
                time.sleep(2)

        if self._controller and self._controller.is_connected():
            logger.info("Discovery[%d] and connection[%d] took %ds" % (
                        self._discovery_duration,
                        self._connect_duration,
                        self._discovery_duration + self._connect_duration))
            return self._controller.mac_address
        else:
            logger.info("Failed to onboard a Nuimo after %s attempts" %
                        self._nuimo_onboarding_attempts)
            return None

    def _start_onboarding(self):
        """
        Blocking. Detects and connects to a nuimo, restarts BT on timeout.

        Initiates the discovery process which blocks until the nuimo
        is found and connected or it timed out.
        """
        logger.debug("Staring discovery timer [%ss]" % DISCOVERY_TIMEOUT)
        self._discovery_timeout_timer = threading.Timer(DISCOVERY_TIMEOUT, self.discovery_timed_out)
        self._discovery_timeout_timer.start()
        self._start_discovery()

    def _start_discovery(self):
        """
        Blocking & asynchronous. Starts the nuimo discovery.

        Initiates the discovery process which triggers the bt module
        to do the scan. Ends in a blocking call that triggers the catching
        of catching of callbacks (asynchronous).
        It is a bit controverse termonology but seems to fit :)

        It the background that call start the d-bus event loop enables
        allows bt related callback methods to be trigerred.

        On succesfull discovery 'controller_discovered' is called
        on timeout 'discovery_timed_out'.
        Both callbacks explicitly call self._manager.stop()
        causing this method to return.

        On success, this is a process which coresponds to the CLI.
        Running:
             root@senic-hub:~# nuimoctl --discover --adapter hci0
             Terminate with Ctrl+C
             Discovered Nuimo controller f5:d4:41:9c:86:b0
             Discovered Nuimo controller e0:88:72:c4:49:c2

        Running the CLI in paralel has an influence on the state
        of self._manager.controllers()
        """

        logger.info("Starting Nuimo onboarding [attempt %s]" % self._nuimo_onboarding_attempts)
        self._is_running = True
        self._discovery_duration = time.time()

        # This will trigger the discovery in terms of a d-bus command.
        # https://github.com/getsenic/gatt-python/blob/master/gatt/gatt_linux.py#L139
        self._manager.start_discovery()
        self._manager.run()

    def discovery_timed_out(self):
        """
        Callback. _start_discovery timed out.

        Stops all bluetooth related actuivity and
        initiates BT restart.
        """

        # Why is this false?
        if not self._is_running:
            return
        logger.info("Discovery timed out")

        self._discovery_duration = None

        if self._connect_timeout_timer:
            self._connect_timeout_timer.cancel()
        if self._controller:
            self._controller.disconnect()

        # The flag needs to be set here because
        # self._manager.stop() unblocks self._start_onboarding()
        self._bt_restart_underway = True
        self._manager.stop_discovery()
        self._manager.stop()

        self.is_running = False
        if self._nuimo_onboarding_attempts != MAX_ONBOARDING_ATTEMPTS:
            self._restart_bluetooth()

    def controller_discovered(self, discovered_nuimo):
        """
        Callback. _start_discovery resulted in a nuimo.

        Stop the timers and the underlying scanning done
        by the bt module.
        Initiate connecting to the discovred nuimo
        """

        logger.debug("Discovered nuimo: %s" % discovered_nuimo.mac_address)
        self._discovery_timeout_timer.cancel()

        if not self._is_running:
            logger.debug("self._is_running is false")
            return
        if self._controller is not None:
            logger.debug("%s discovered but ignored, already connecting to another one", discovered_nuimo.mac_address)
            return
        if self._required_mac_address and (self._required_mac_address.lower() != discovered_nuimo.mac_address.lower()):
            logger.debug("%s discovered but ignored because we look for a specific one", discovered_nuimo.mac_address)
            return

        self._discovery_duration = round(time.time() - self._discovery_duration)
        logger.debug("Discovery took %ss" % self._discovery_duration)

        logger.debug("Stopping nuimo discovery")
        self._manager.stop_discovery()

        self.start_connection(discovered_nuimo)

    def start_connection(self, discovered_nuimo):
        """
        Blocking. Starts the nuimo discovery.

        Initiates the process of connecting to a nuimo and
        the threads to enforce timeout.

        On succesfull connect 'connect_succeeded' is called.
        On failure:
         * by timeout 'connect_timed_out'
         * or fail response from the underlying libs - 'connect_failed'
        """

        self._connect_timeout_timer = threading.Timer(CONNECTION_TIMEOUT, self.connect_timed_out)
        logger.debug("Starting thread for connection timeout[%s]" % CONNECTION_TIMEOUT)
        self._connect_timeout_timer.start()
        self._controller = discovered_nuimo
        self._controller.listener = self
        logger.debug("Trying to connect to nuimo: %s" % discovered_nuimo.mac_address)
        self._connect_duration = time.time()
        self._controller.connect()

    def connect_succeeded(self):
        if not self._is_running:
            return
        logger.debug("%s successfully connected, stopping now", self._controller.mac_address)
        self._nuimo_connected = True
        if self._connect_timeout_timer:
            self._connect_timeout_timer.cancel()

            self._connect_duration = round(time.time() - self._connect_duration)
            logger.debug("Connecting took %ss" % self._connect_duration)

        self._manager.stop()

    def connect_failed(self, error):
        """
        Callback. start_connection failed.

        There can be multiple underlying reasons for having
        the connection fail.
        https://github.com/getsenic/gatt-python/blob/master/gatt/gatt_linux.py#L297

        For the current solution we're all the reasons as
        issues that can be sloved by restarting the module.
        This might change with new insights.

        For that case we're actin as the connection timed
        out.
        """

        # This is to identify failing cases different from a timeout.
        logger.info("%s connection failed (didn't timeout): %s", self._controller.mac_address, error)
        self.connect_timed_out()

    def connect_timed_out(self):
        """
        Callback. start_connection timed out.

        Stops all bluetooth related actuivity and
        initiates BT restart.

        Couldn't find an explicit method that will cancel
        the blocking connect on a timeout (this method when traced down):
        https://github.com/getsenic/gatt-python/blob/master/gatt/gatt_linux.py#L282
        am assuming that ending with self._restart_bluetooth()
        eliminates the need for it. Do question the approach.
        """

        if not self._is_running:
            return

        logger.info("Connect failed due to timeout")

        # Restoring duration to initial state
        self._connect_duration = None

        # The flag needs to be set here because
        # self._manager.stop() unblocks self._start_onboarding()
        self._bt_restart_underway = True
        self._manager.stop()
        self.is_running = False

        if self._nuimo_onboarding_attempts != MAX_ONBOARDING_ATTEMPTS:
            self._restart_bluetooth()
