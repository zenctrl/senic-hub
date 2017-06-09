#!/usr/bin/python3

import click
import logging
import time
from subprocess import call, CalledProcessError, check_output, STDOUT, TimeoutExpired
from threading import Thread

from .bluez_peripheral import Peripheral
from .bluenet_gatt_service import BluenetService, BluenetUuids, WifiConnectionState

#: Name of the NetworkManager connection to use for BLE onboarding
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
@click.option('--verbose', '-v', is_flag=True, help="Print verbose messages (log level DEBUG)")
@click.pass_context
def bluenet_start(ctx, hostname, alias, verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    ctx.obj.run(hostname, alias)


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
    Daemon to enable Wifi onboarding via Bluetooth Low Energy.
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
        self._current_ssid = None
        self._is_joining_wifi = False

    def run(self, hostname, bluetooth_alias):
        # prepare BLE GATT Service:
        peripheral = Peripheral(bluetooth_alias, self._bluetooth_adapter)
        gatt_service = BluenetService(peripheral.bus, 0, hostname, "1.0")
        gatt_service.set_callback_to_join_network(self.join_network)
        self._gatt_service = gatt_service
        peripheral.add_service(gatt_service)
        peripheral.add_advertised_service_uuid(BluenetUuids.SERVICE)

        # create thread to scan for networks:
        scan_thread = Thread(target=self._scan_wifi_loop, daemon=True)
        scan_thread.start()

        # create thread to poll for connection status:
        connection_state_thread = Thread(target=self._run_wifi_status_loop, daemon=True)
        connection_state_thread.start()

        peripheral.run()

    def join_network(self, ssid, credentials):
        logger.info("Trying to join network: %s, Credentials: %s" % (ssid, credentials))
        self._configure_wlan(ssid, credentials)

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

            self._gatt_service.set_available_networks(found_ssids.keys())

        while True:
            if not self._is_joining_wifi:
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

        while True:
            new_status = self.get_wifi_status()
            if new_status != status:
                print_status(new_status)
                self._gatt_service.set_connection_state(new_status, self._current_ssid)
                status = new_status
            time.sleep(1)

    def _configure_wlan(self, ssid, password):
        self._is_joining_wifi = ssid is not None

        logger.info("=> nmcli con delete %s" % NM_CONNECTION_NAME)
        call(['nmcli', 'con', 'delete', NM_CONNECTION_NAME])

        if ssid and password:
            logger.info("=> nmcli dev wifi con %s password %s ifname %s name %s" %
                        (ssid, password, self._wlan_adapter, NM_CONNECTION_NAME))
            call(['nmcli', 'dev', 'wifi', 'con', ssid, 'password', password, 'ifname', self._wlan_adapter, 'name', NM_CONNECTION_NAME])
        elif ssid:
            logger.info("=> nmcli dev wifi con %s ifname %s name %s" %
                        (ssid, self._wlan_adapter, NM_CONNECTION_NAME))
            call(['nmcli', 'dev', 'wifi', 'con', ssid, 'ifname', self._wlan_adapter, 'name', NM_CONNECTION_NAME])

        self._is_joining_wifi = False


if __name__ == '__main__':
    bluenet_cli()
