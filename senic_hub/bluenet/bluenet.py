#!/usr/bin/python3

import click
import dbus
import dbus.mainloop.glib
import logging
import time
from threading import Thread
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

import NetworkManager
try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject

from .bluez_peripheral import Peripheral
from .bluenet_gatt_service import BluenetService, BluenetUuids, WifiConnectionState

#: Name of the NetworkManager connection to use for BLE provisioning
#: It will be created on first attempt to join a network
#: or overwritten if it already exists.
NM_CONNECTION_NAME = 'bluenet'

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
    log_format = '%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)
    ctx.obj.join_network(ssid, password)


@bluenet_cli.command(name='status', help="print Wifi status")
def bluenet_status():
    nm_state = NetworkManager.NetworkManager.State
    if nm_state >= NetworkManager.NM_STATE_CONNECTED_GLOBAL:
        status = WifiConnectionState.CONNECTED
    elif nm_state > NetworkManager.NM_STATE_DISCONNECTING:
        status = WifiConnectionState.CONNECTING
    else:
        status = WifiConnectionState.DISCONNECTED
    print(status)


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
        self._wifi_status = WifiConnectionState.DOWN

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

        # create thread to scan for networks:
        scan_thread = Thread(target=self._scan_wifi_loop, daemon=True)
        scan_thread.start()

        # create thread to listen for connection state changes:
        connection_state_thread = Thread(target=self._listen_for_wifi_state_changes, daemon=True)
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

    def _scan_wifi_loop(self, waitsec=20, discard_time=60):
        found_ssids = {}

        def scan_wifi_networks():
            ssids = []
            for dev in NetworkManager.NetworkManager.GetDevices():
                if dev.DeviceType != NetworkManager.NM_DEVICE_TYPE_WIFI:
                    continue
                for ap in dev.GetAccessPoints():
                    ssids.append(ap.Ssid)

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
                    self._wifi_status == WifiConnectionState.DISCONNECTED):
                logger.info("Known network reappeared, trying to reconnect to it.")
                # Actually this should be done by NetworkManager automatically (because
                # 'autoconnect' flag is true by default) but this doesn't work reliable
                # (see for example https://bugs.launchpad.net/ubuntu/+source/network-manager/+bug/1354924)
                connection = self._get_nm_connection()
                device = self._get_nm_device()
                if connection and device:
                    NetworkManager.NetworkManager.ActivateConnection(connection, device, "/")

            self._gatt_service.set_available_networks(found_ssids.keys())

        while True:
            if self._ble_peripheral.is_advertising and not self._is_joining_wifi:
                scan_wifi_networks()
            time.sleep(waitsec)

    def _listen_for_wifi_state_changes(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        def print_status(status, nm_state):
            if status in (WifiConnectionState.CONNECTING, WifiConnectionState.CONNECTED):
                logger.info("Wifi status changed: %s (%d) to %s" % (status, nm_state, self._current_ssid))
            else:
                logger.info("Wifi status changed: %s (%d)" % (status, nm_state))

        def on_state_changed(nm_instance, nm_state, **kwargs):

            if nm_state >= NetworkManager.NM_STATE_CONNECTED_GLOBAL:
                new_status = WifiConnectionState.CONNECTED
            elif nm_state > NetworkManager.NM_STATE_DISCONNECTING:
                new_status = WifiConnectionState.CONNECTING
            else:
                new_status = WifiConnectionState.DISCONNECTED

            self._update_current_ssid()

            if new_status == self._wifi_status:
                return

            print_status(new_status, nm_state)
            self._wifi_status = new_status
            self._on_wifi_status_changed()

        # check initial status:
        initial_state = NetworkManager.NetworkManager.State
        on_state_changed(None, initial_state)

        # listen for changes:
        NetworkManager.NetworkManager.OnStateChanged(on_state_changed)
        logger.debug("Start listening to network status changes")
        # Attention: a GObject.MainLoop() is required for this to work
        # in this case it is started by the BLE Peripheral object

    def _update_current_ssid(self):
        connection = self._get_nm_connection()
        if connection:
            self._current_ssid = connection.GetSettings().get('802-11-wireless', {}).get('ssid', '')
        else:
            self._current_ssid = ''

    def _configure_wlan(self, ssid, password):
        device = self._get_nm_device()
        if not device:
            logger.error("Couldn't find the requested network adapter")
            return

        self._is_joining_wifi = ssid is not None

        # delete connection if it already exists:
        connection = self._get_nm_connection()
        if connection:
            logger.info("Deleting connection %s" % NM_CONNECTION_NAME)
            connection.Delete()

        if ssid and password:
            logger.info("Creating connection to %s with %s named %s" %
                        (ssid, self._wlan_adapter, NM_CONNECTION_NAME))
            connection_params = {
                'connection': {
                    'id': NM_CONNECTION_NAME,
                    'type': '802-11-wireless',
                },
                '802-11-wireless': {
                    'mode': 'infrastructure',
                    'ssid': ssid,
                },
                '802-11-wireless-security': {
                    'key-mgmt': 'wpa-psk',
                    'psk': password,
                },
            }
            NetworkManager.NetworkManager.AddAndActivateConnection(connection_params, device, "/")
        elif ssid:
            logger.info("Creating passwordless connection to %s with %s named %s" %
                        (ssid, self._wlan_adapter, NM_CONNECTION_NAME))
            connection_params = {
                'connection': {
                    'id': NM_CONNECTION_NAME,
                    'type': '802-11-wireless',
                },
                '802-11-wireless': {
                    'mode': 'infrastructure',
                    'ssid': ssid,
                },
            }
            NetworkManager.NetworkManager.AddAndActivateConnection(connection_params, device, "/")

        self._is_joining_wifi = False

    def _on_wifi_status_changed(self):
        self._gatt_service.set_connection_state(self._wifi_status, self._current_ssid)
        if self._wifi_status == WifiConnectionState.CONNECTED:
            self._update_hostname()
        self._update_advertising_state()

    def _update_advertising_state(self):
        if (self._auto_advertise and
                self._wifi_status == WifiConnectionState.CONNECTED and
                not self._ble_peripheral.is_connected and
                self._ble_peripheral.is_advertising):
            # re-enabling advertisement is not possible while a device is connected
            # because of that we are not disabling it in the first place when a device is connected
            logging.info("Wifi connected. Stopping BLE advertisement.")
            self._ble_peripheral.stop_advertising()
        elif (not self._ble_peripheral.is_advertising and
                (not self._auto_advertise or self._wifi_status == WifiConnectionState.DISCONNECTED)):
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
        device = self._get_nm_device()
        if not device:
            logger.error("Couldn't find the requested network adapter")
            return None

        if not device.Ip4Config:
            return None

        addresses = device.Ip4Config.AddressData
        if addresses:
            return addresses[0].get('address', None)

    def _get_nm_connection(self):
        try:
            connections = NetworkManager.Settings.ListConnections()
            connections_by_name = dict([(x.GetSettings()['connection']['id'], x) for x in connections])
        except AttributeError as e:
            logger.warning("Error while trying to get NetworkManager connection: %s" % e)
            return None
        return connections_by_name.get(NM_CONNECTION_NAME, None)

    def _get_nm_device(self):
        try:
            devices = NetworkManager.NetworkManager.GetDevices()
            devices_by_name = dict([(d.Interface, d) for d in devices])
        except AttributeError as e:
            logger.warning("Error while trying to get NetworkManager device: %s" % e)
            return None
        return devices_by_name.get(self._wlan_adapter, None)

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
