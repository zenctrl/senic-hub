from enum import Enum
import logging

import dbus

try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject

from .dbus_bluez_interfaces import Characteristic, Service, string_to_dbus_array

logger = logging.getLogger(__name__)


class BluenetUuids(object):
    SERVICE = 'FBE51523-B3E6-4F68-B6DA-410C0BBA1A78'

    AVAILABLE_NETWORKS = 'FBE51524-B3E6-4F68-B6DA-410C0BBA1A78'
    CONNECTION_STATE = 'FBE51525-B3E6-4F68-B6DA-410C0BBA1A78'
    HOST_NAME = 'FBE51526-B3E6-4F68-B6DA-410C0BBA1A78'
    VERSION = 'FBE51527-B3E6-4F68-B6DA-410C0BBA1A78'

    SSID = 'FBE51528-B3E6-4F68-B6DA-410C0BBA1A78'
    CREDENTIALS = 'FBE51529-B3E6-4F68-B6DA-410C0BBA1A78'


class WifiConnectionState(Enum):
    DOWN = 0
    DISCONNECTED = 1
    CONNECTING = 2
    CONNECTED = 3


class BluenetService(Service):
    """
    Concrete implementation of a GATT service that can be used for Wifi onboarding.
    """
    
    def __init__(self, bus, index, host_name, version):
        super().__init__(bus, index, BluenetUuids.SERVICE, True)
        self._join_callback = None
        self._available_networks_characteristic = AvailableNetworksCharacteristic(bus, 0, self)
        self._connection_state_characteristic = ConnectionStateCharacteristic(bus, 1, self)
        self._host_name_characteristic = HostNameCharacteristic(bus, 2, self, host_name)
        self._version_characteristic = VersionCharacteristic(bus, 3, self, version)
        self._ssid_characteristic = SsidCharacteristic(bus, 4, self)
        self._credentials_characteristic = CredentialsCharacteristic(bus, 5, self)

        self._credentials_characteristic.set_callback_on_change(self._credentials_received)

        self.add_characteristic(self._available_networks_characteristic)
        self.add_characteristic(self._connection_state_characteristic)
        self.add_characteristic(self._host_name_characteristic)
        self.add_characteristic(self._version_characteristic)
        self.add_characteristic(self._ssid_characteristic)
        self.add_characteristic(self._credentials_characteristic)

    def set_available_networks(self, ssids):
        self._available_networks_characteristic.ssids = ssids

    def set_connection_state(self, state, current_ssid):
        self._connection_state_characteristic.set_connection_state(state, current_ssid)

    def set_callback_to_join_network(self, cb):
        """
        The provided callback will be called when the credentials for a network were received.
        It must have the signature callback(ssid, credentials).
        """
        self._join_callback = cb

    def _credentials_received(self):
        if callable(self._join_callback):
            self._join_callback(
                self._ssid_characteristic.ssid, self._credentials_characteristic.credentials)
        
        
class AvailableNetworksCharacteristic(Characteristic):
    """
    GATT characteristic sending a list of network names.
    
    Possible operations: Notify
    Sends one SSID at a time with each notify signal.
    After all SSIDs have been sent it waits for 3s and starts from begin.
    """

    def __init__(self, bus, index, service):
        super().__init__(bus, index, BluenetUuids.AVAILABLE_NETWORKS, ['notify'], service)
        self._notifying = False
        self.ssids = []
        self._ssids_sent = []
        self._ssid_last_sent = ''
        self._update_interval = 300  # ms, time between single SSIDs
        self._wait_time = 3000  # ms, time to wait between sending the complete set of SSIDs

    def _send_next_ssid(self):
        if not self.ssids:
            logger.debug("No SSIDs available.")
            return self._notifying

        next_ssid = ''
        for ssid in self.ssids:
            if ssid not in self._ssids_sent:
                next_ssid = ssid
                break

        if not next_ssid:
            # all SSIDs have been sent at least once, repeat:
            self._ssids_sent = []
            GObject.timeout_add(self._wait_time, self._start_send_ssids)
            return False

        logger.debug("Sending next SSID: %s" % next_ssid)

        self.value_update(string_to_dbus_array(next_ssid))

        self._ssid_last_sent = next_ssid
        self._ssids_sent.append(next_ssid)

        return self._notifying

    def _start_send_ssids(self):
        GObject.timeout_add(self._update_interval, self._send_next_ssid)
        # return False to stop timeout:
        return False

    def _read_value(self, options):
        logger.info("Sending AvailableNetworks Value")
        return string_to_dbus_array(self._ssid_last_sent)

    def _start_notify(self):
        if self._notifying:
            logger.info("Already notifying, nothing to do")
            return

        logger.info("Start notifying about available networks")
        self._notifying = True
        self._ssids_sent = []
        self._start_send_ssids()

    def _stop_notify(self):
        if not self._notifying:
            logger.info("Not notifying, nothing to do")
            return

        logger.info("Stop notifying about available networks")
        self._notifying = False

    def remote_disconnected(self):
        self._stop_notify()


class ConnectionStateCharacteristic(Characteristic):
    """
    GATT characteristic sending the current Wifi connection status.
    
    Possible operations: Read + Notify
    First byte  is the connection status (0: Down 1: Disconnected, 2: Connecting, 3: Connected)
    In case of Connecting or Connected the remaining bytes are the currently used SSID.
    """

    def __init__(self, bus, index, service):
        super().__init__(bus, index, BluenetUuids.CONNECTION_STATE, ['read', 'notify'], service)
        self._notifying = False
        self.state = WifiConnectionState.DISCONNECTED
        self.current_ssid = None

    def set_connection_state(self, state, current_ssid):
        self.state = state
        self.current_ssid = current_ssid
        if self._notifying:
            logger.info("Sending updated connection state")
            if self.state != WifiConnectionState.DISCONNECTED and self.current_ssid:
                self.value_update([dbus.Byte(self.state.value)] + string_to_dbus_array(self.current_ssid))
            else:
                self.value_update([dbus.Byte(self.state.value)])

    def _read_value(self, options):
        logger.info("Read Connection State Value")
        if self.state != WifiConnectionState.DISCONNECTED and self.current_ssid:
            return [dbus.Byte(self.state.value)] + string_to_dbus_array(self.current_ssid)
        else:
            return [dbus.Byte(self.state.value)]

    def _start_notify(self):
        logger.info("Enabled notification about connection state.")
        self._notifying = True

    def _stop_notify(self):
        logger.info("Disabled notification about connection state.")
        self._notifying = False


class HostNameCharacteristic(Characteristic):
    """
    GATT characteristic providing the host name of the server.
    
    Possible operations: Read
    Content: host name as array of characters
    """

    def __init__(self, bus, index, service, host_name):
        super().__init__(bus, index, BluenetUuids.HOST_NAME, ['read'], service)
        self.host_name = host_name

    def _read_value(self, options):
        logger.info("Sending HostName Value")
        return string_to_dbus_array(self.host_name)


class VersionCharacteristic(Characteristic):
    """
    GATT characteristic providing the version of this GATT service.
    
    Possible operations: Read
    Content: Version as a string (array of characters)
    """

    def __init__(self, bus, index, service, version):
        super().__init__(bus, index, BluenetUuids.VERSION, ['read'], service)
        self.version = version

    def _read_value(self, options):
        logger.info("Sending Version Value")
        return string_to_dbus_array(self.version)

        
class SsidCharacteristic(Characteristic):
    """
    GATT characteristic for setting the SSID to connect with.
    An attempt to join the network is made when the credentials are received.
    
    Possible operations: Write
    Content: SSID as array of characters
    """

    def __init__(self, bus, index, service):
        super().__init__(bus, index, BluenetUuids.SSID, ['write'], service)
        self.ssid = None

    def _write_value(self, value, options):
        self.ssid = bytes(value).decode()
        logger.info("Received SSID: %s" % self.ssid)
        
        
class CredentialsCharacteristic(Characteristic):
    """
    GATT characteristic for providing the credentials needed to join a network.
    When this characteristic is written an attempt is made to join the specified network.
    
    Possible operations: Write
    Content: Credentials (i.e. Wifi password) as array of characters
    """

    def __init__(self, bus, index, service):
        super().__init__(bus, index, BluenetUuids.CREDENTIALS, ['write'], service)
        self.credentials = None
        self.callback = None

    def set_callback_on_change(self, cb):
        self.callback = cb

    def _write_value(self, value, options):
        self.credentials = bytes(value).decode()
        logger.info("Received password: %s" % self.credentials)
        if callable(self.callback):
            self.callback()
