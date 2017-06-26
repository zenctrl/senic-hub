#!/usr/bin/python3

import click
import logging
import time
from subprocess import call, CalledProcessError, check_output, STDOUT, TimeoutExpired
from threading import Thread
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

from .bluez_peripheral import Peripheral
from .bluenet_gatt_service import BluenetService, BluenetUuids, WifiConnectionState

#: Name of the NetworkManager connection to use for BLE provisioning
#: It will be created on first attempt to join a network
#: or overwritten if it already exists.
NM_CONNECTION_NAME = 'Bluenet'

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
@click.option('--wlan', '-w', required=False, help="WLAN device (default = wlan0)")
@click.option('--bluetooth', '-b', required=False, help="Bluetooth device")
def bluenet_cli(ctx, wlan, bluetooth):
    if not wlan:
        wlan = 'wlan0'
    ctx.obj = BluenetDaemon(wlan, bluetooth)


@bluenet_cli.command(name='start', help="start GATT service and scan for networks")
@click.option('--hostname', '-h', required=True, help="Host Name of Hub")
@click.option('--alias', '-a', required=True, help="Bluetooth Alias Name")
@click.option('--verbose', '-v', count=True, help="Print info messages (-vv for debug messages)")
@click.option('--auto-advertise', is_flag=True, help="Disable BLE advertising when not needed")
@click.pass_context
def bluenet_start(ctx, hostname, alias, verbose, auto_advertise):
    log_format = '%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s'
    if verbose >= 2:
        logging.basicConfig(level=logging.DEBUG, format=log_format)
    elif verbose >= 1:
        logging.basicConfig(level=logging.INFO, format=log_format)
    else:
        logging.basicConfig(level=logging.WARNING, format=log_format)
    ctx.obj.run(hostname, alias, auto_advertise)


@bluenet_cli.command(name='join', help="only join Wifi")
@click.option('--ssid', '-s', required=True, help="SSID of the network")
@click.option('--password', '-p', required=True, help="Wifi password")
@click.pass_context
def bluenet_join(ctx, ssid, password):
    ctx.obj.join_network(ssid, password)


@bluenet_cli.command(name='status', help="print Wifi status")
@click.pass_context
def bluenet_status(ctx):
    print(ctx.obj.get_wifi_status())


class BluenetDaemon(object):
    """
    Daemon to enable Wifi provisioning via Bluetooth Low Energy.
    The run() method creates the Bluetooth GATT server and starts threads to listen for new networks 
    and changes in the connection status.
    """

    def __init__(self, wlan_adapter, bluetooth_adapter):
        """
        Initializes the object. It can then be started with run().
        :param wlan_adapter: name of the WLAN adapter (i.e. 'wlan0')
        :param bluetooth_adapter: name of the bluetooth adapter (i.e. 'hci0')
        """
        self._wlan_adapter = wlan_adapter
        self._bluetooth_adapter = bluetooth_adapter
        self._gatt_service = None
        self._ble_peripheral = None
        self._current_ssid = None
        self._is_joining_wifi = False
        self._auto_advertise = False
        self._hostname = None
        self._join_thread = None

    def run(self, hostname, bluetooth_alias, auto_advertise):
        self._hostname = hostname
        self._auto_advertise = auto_advertise

        # prepare BLE GATT Service:
        self._ble_peripheral = Peripheral(bluetooth_alias, self._bluetooth_adapter)
        gatt_service = BluenetService(self._ble_peripheral.bus, 0, self._get_hostname(), "1.0")
        gatt_service.set_credentials_received_callback(self.join_network)
        self._gatt_service = gatt_service
        self._ble_peripheral.add_service(gatt_service)
        self._ble_peripheral.add_advertised_service_uuid(BluenetUuids.SERVICE)
        self._ble_peripheral.on_remote_disconnected = self._update_advertising_state

        self._update_advertising_state()

        # create thread to scan for networks:
        scan_thread = Thread(target=self._scan_wifi_loop, daemon=True)
        scan_thread.start()

        # create thread to poll for connection status:
        connection_state_thread = Thread(target=self._run_wifi_status_loop, daemon=True)
        connection_state_thread.start()

        # create thread for rpc server:
        rpc_thread = Thread(target=self._start_rpc_server, daemon=True)
        rpc_thread.start()

        self._ble_peripheral.run()

    def join_network(self, ssid, credentials):
        logger.info("Trying to join network: %s" % ssid)
        logger.debug("Password: %s" % credentials)
        if self._join_thread and self._join_thread.is_alive():
            logger.warning("Cannot join network while previous joining is still in process")
        else:
            # using a new thread to join the network because this is a blocking operation
            # and would otherwise prevent Bluetooth from sending the characteristic write response
            self._join_thread = Thread(target=self._configure_wlan, args=(ssid, credentials))
            self._join_thread.start()

    def get_wifi_status(self):
        # get current SSID:
        try:
            connection_status = check_output(
                ['nmcli', '-f', '802-11-wireless.ssid', 'connection', 'show', NM_CONNECTION_NAME],
                timeout=5, stderr=STDOUT).decode()
        except CalledProcessError as e:
            if e.returncode == 10:
                # means connection NM_CONNECTION_NAME doesn't exist
                connection_status = ''
            else:
                logger.warning("Wifi status error: %s" % e)
                return WifiConnectionState.DOWN
        except TimeoutExpired as e:
            logger.warning("Wifi status error: %s" % e)
            return WifiConnectionState.DOWN

        if '802-11-wireless.ssid:' in connection_status:
            self._current_ssid = connection_status.split("ssid:")[1].strip()
        else:
            self._current_ssid = ''

        # get connection status:
        try:
            device_status = check_output(
                ['nmcli', '-f', 'general.state', 'device', 'show', self._wlan_adapter],
                timeout=5, stderr=STDOUT).decode()
        except (CalledProcessError, TimeoutExpired) as e:
            logger.warning("Wifi status error: %s" % e)
            return WifiConnectionState.DOWN

        if '100' in device_status:
            return WifiConnectionState.CONNECTED
        elif '50' in device_status:
            return WifiConnectionState.CONNECTING
        else:
            return WifiConnectionState.DISCONNECTED

    def _scan_wifi_loop(self, waitsec=20, discard_time=60):
        found_ssids = {}

        def scan_wifi_networks():
            try:
                iw_scan_result = check_output(['iw', 'dev', self._wlan_adapter, 'scan']).decode()
            except CalledProcessError as e:
                logger.warning("Scanning wifi networks failed: %s" % e)
                return

            ssids = []
            for line in iw_scan_result.split('\n'):
                if 'SSID: ' in line:
                    ssid = line.split('SSID: ', 1)[1]
                    if ssid:
                        ssids.append(ssid)

            for ssid in ssids:
                if ssid not in found_ssids:
                    logger.info("New network found: %s" % ssid)
                found_ssids[ssid] = time.time()

            # Remove networks that we didn't see for a while
            now = time.time()
            for ssid, last_seen in found_ssids.copy().items():
                if now - last_seen > discard_time:
                    logger.info("Network disappeared: %s" % ssid)
                    del found_ssids[ssid]

            if (self._current_ssid in found_ssids and
                    self.get_wifi_status() == WifiConnectionState.DISCONNECTED):
                logger.info("Known network reappeared, trying to reconnect to it.")
                # Actually this should be done by NetworkManager automatically (because
                # 'autoconnect' flag is true by default) but this doesn't work reliable
                # (see for example https://bugs.launchpad.net/ubuntu/+source/network-manager/+bug/1354924)
                try:
                    call(['nmcli', 'con', 'up', NM_CONNECTION_NAME])
                except CalledProcessError as e:
                    logger.warning("Error while trying to bring network back up: %s" % e)

            self._gatt_service.set_available_networks(found_ssids.keys())

        while True:
            if self._ble_peripheral.is_advertising and not self._is_joining_wifi:
                scan_wifi_networks()
            time.sleep(waitsec)

    def _run_wifi_status_loop(self):
        status = self.get_wifi_status()
        self._gatt_service.set_connection_state(status, self._current_ssid)

        def print_status(status):
            if status in (WifiConnectionState.CONNECTING, WifiConnectionState.CONNECTED):
                logger.info("Wifi status changed: %s to %s" % (status, self._current_ssid))
            else:
                logger.info("Wifi status changed: %s" % status)

        print_status(status)

        last_status_changed_time = time.time()
        while True:
            new_status = self.get_wifi_status()
            if new_status != status:
                print_status(new_status)
                if (self._is_joining_wifi and
                        new_status == WifiConnectionState.DISCONNECTED and
                        time.time() - last_status_changed_time < 10.0):
                    # When WiFi adapter was already connected, the WiFi state will change
                    # from `connecting` to `disconnected` to `connected`. To prevent
                    # `disconnected` to be notified, we wait 5 seconds if we actually
                    # succeed to connect after a intermediate disconnect step.
                    logger.info("Ignoring state change to DISCONNECTED as we are trying to connect to a network")
                else:
                    status = new_status
                    self._on_wifi_status_changed(status)
                    last_status_changed_time = time.time()
            if self._ble_peripheral.is_connected:
                time.sleep(1)
            else:
                # NetworkManager is slow at detecting connection changes
                # -> checking every 30s is enough while setup app is not connected
                # (when Wifi router is turned off connection status will be "Connecting"
                # for 2 minutes before going to "Disconnected")
                time.sleep(30)

    def _configure_wlan(self, ssid, password):
        self._is_joining_wifi = ssid is not None

        logger.info("=> nmcli con delete %s" % NM_CONNECTION_NAME)
        call(['nmcli', 'con', 'delete', NM_CONNECTION_NAME])

        if ssid and password:
            logger.info("=> nmcli dev wifi con %s password *** ifname %s name %s" %
                        (ssid, self._wlan_adapter, NM_CONNECTION_NAME))
            call([
                'nmcli', 'dev', 'wifi',
                'con', ssid,
                'password', password,
                'ifname', self._wlan_adapter,
                'name', NM_CONNECTION_NAME])
        elif ssid:
            logger.info("=> nmcli dev wifi con %s ifname %s name %s" %
                        (ssid, self._wlan_adapter, NM_CONNECTION_NAME))
            call([
                'nmcli', 'dev', 'wifi',
                'con', ssid,
                'ifname', self._wlan_adapter,
                'name', NM_CONNECTION_NAME])

        self._is_joining_wifi = False

    def _on_wifi_status_changed(self, new_status):
        self._gatt_service.set_connection_state(new_status, self._current_ssid)
        if new_status == WifiConnectionState.CONNECTED:
            self._update_hostname()
        self._update_advertising_state(new_status)

    def _update_advertising_state(self, wifi_status=None):
        if not wifi_status:
            wifi_status = self.get_wifi_status()
        if (self._auto_advertise and
                wifi_status == WifiConnectionState.CONNECTED and
                not self._ble_peripheral.is_connected and
                self._ble_peripheral.is_advertising):
            # re-enabling advertisement is not possible while a device is connected
            # because of that we are not disabling it in the first place when a device is connected
            logging.info("Wifi connected. Stopping BLE advertisement.")
            self._ble_peripheral.stop_advertising()
        elif (not self._ble_peripheral.is_advertising and
                (not self._auto_advertise or wifi_status == WifiConnectionState.DISCONNECTED)):
            logging.info("Starting BLE advertisement to be able to "
                         "use the setup app to reconfigure Wifi.")
            self._ble_peripheral.start_advertising()

    def _update_hostname(self):
        hostname = self._get_hostname()
        logger.info("New hostname: %s" % hostname)
        self._gatt_service.set_hostname(hostname)

    def _get_hostname(self):
        if '%IP' in self._hostname:
            ip = self._get_ip_address()
            if ip:
                return self._hostname.replace('%IP', ip)
            else:
                return ''
        else:
            return self._hostname

    def _get_ip_address(self):
        try:
            ifconfig_output = check_output(['ifconfig', self._wlan_adapter]).decode()
        except CalledProcessError as e:
            logger.warning("ifconfig error: %s" % e)
            return None

        if 'addr:' not in ifconfig_output:
            return None

        ip = ifconfig_output.split('addr:', 1)[1].split(' ', 1)[0]
        return ip

    def _start_rpc_server(self):
        def is_bluenet_connected():
            return self._ble_peripheral.is_connected

        server = SimpleXMLRPCServer(('127.0.0.1', 6459), requestHandler=RequestHandler)
        server.register_function(is_bluenet_connected)
        logger.info("Starting RPC server")
        server.serve_forever()


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


if __name__ == '__main__':
    bluenet_cli()
