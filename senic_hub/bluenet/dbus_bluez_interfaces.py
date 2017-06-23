import logging

import dbus
import dbus.exceptions
import dbus.service

logger = logging.getLogger(__name__)

BLUEZ_SERVICE_NAME = 'org.bluez'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'

GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHARACTERISTIC_IFACE = 'org.bluez.GattCharacteristic1'
GATT_DESCRIPTOR_IFACE = 'org.bluez.GattDescriptor1'

LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
LE_ADVERTISEMENT_IFACE = 'org.bluez.LEAdvertisement1'


class Application(dbus.service.Object):
    """
    org.freedesktop.DBus.ObjectManager interface implementation

    This class is a DBus object manager for GattService1 objects.
    """

    def __init__(self, bus):
        self.path = '/CustomGattApplication'
        super().__init__(bus, self.path)
        self.services = []

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}

        for service in self.services:
            response[service.get_path()] = service.get_properties()

            for characteristic in service.get_characteristics():
                response[characteristic.get_path()] = characteristic.get_properties()

                for descriptor in characteristic.get_descriptors():
                    response[descriptor.get_path()] = descriptor.get_properties()

        return response


class Service(dbus.service.Object):
    """
    org.bluez.GattService1 interface implementation

    This is intended to be subclassed with a concrete implementation.
    """

    #: base of the path to this D-Bus object (can be overwritten)
    PATH_BASE = '/org/bluez/bluenet/service'

    def __init__(self, bus, index, uuid, primary):
        self.path = self.PATH_BASE + str(index)
        super().__init__(bus, self.path)
        self.bus = bus
        self.uuid = uuid  # string
        self.primary = primary  # bool
        self.characteristics = []

    def get_properties(self):
        return {
            GATT_SERVICE_IFACE: {
                'UUID': self.uuid,
                'Primary': self.primary,
                'Characteristics': dbus.Array(
                    self.get_characteristic_paths(),
                    signature='o')
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_characteristic_paths(self):
        return [c.get_path() for c in self.characteristics]

    def get_characteristics(self):
        return self.characteristics

    def remote_disconnected(self):
        """
        This is a newly introduced method that should be called when the remote device disconnected.
        This is necessary to be able to stop notifying (BlueZ doesn't call StopNotify when device disconnects).
        """
        for characteristic in self.characteristics:
            characteristic.remote_disconnected()

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_SERVICE_IFACE]

    @dbus.service.signal(DBUS_PROP_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass


class Characteristic(dbus.service.Object):
    """
    org.bluez.GattCharacteristic1 interface implementation

    This is intended to be subclassed with a concrete implementation.
    """

    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + '/char' + str(index)
        super().__init__(bus, self.path)
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.descriptors = []
        self._is_notifying = False

    def get_properties(self):
        return {
            GATT_CHARACTERISTIC_IFACE: {
                'Service': self.service.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags,
                'Descriptors': dbus.Array(
                    self.get_descriptor_paths(),
                    signature='o')
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_descriptor(self, descriptor):
        self.descriptors.append(descriptor)

    def get_descriptor_paths(self):
        return [d.get_path() for d in self.descriptors]

    def get_descriptors(self):
        return self.descriptors

    def value_update(self, byte_array):
        self.PropertiesChanged(GATT_CHARACTERISTIC_IFACE, {'Value': byte_array}, [])

    @property
    def is_notifying(self):
        return self._is_notifying

    def _read_value(self, options):
        """
        Called when the remote tries to read this characteristic.
        Should return a dbus byte array.
        """
        logger.warning("Default Char ReadValue called, returning error")
        raise NotSupportedException()

    def _write_value(self, value, options):
        """
        Called when the remote tries to write to this characteristic.
        """
        logger.warning("Default Char WriteValue called, returning error")
        raise NotSupportedException()

    def _on_start_notifying(self):
        """
        Called when the remote subscribes to changes for this characteristic.
        """
        pass

    def _on_stop_notifying(self):
        """
        Called when the remote unsubscribes from changes for this characteristic.
        """
        pass

    def remote_disconnected(self):
        """
        Called when the remote device disconnected.
        Calls _stop_notify() to stop notifying characteristic changes,
        because BlueZ doesn't call StopNotify when the remote device disconnects.
        """
        self.StopNotify()

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_CHARACTERISTIC_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_CHARACTERISTIC_IFACE]

    @dbus.service.method(GATT_CHARACTERISTIC_IFACE, in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        return self._read_value(options)

    @dbus.service.method(GATT_CHARACTERISTIC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        self._write_value(value, options)

    @dbus.service.method(GATT_CHARACTERISTIC_IFACE)
    def StartNotify(self):
        if self.is_notifying:
            return
        self._is_notifying = True
        self._on_start_notifying()

    @dbus.service.method(GATT_CHARACTERISTIC_IFACE)
    def StopNotify(self):
        if not self.is_notifying:
            return
        self._is_notifying = False
        self._on_stop_notifying()

    @dbus.service.signal(DBUS_PROP_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass


class Descriptor(dbus.service.Object):
    """
    org.bluez.GattDescriptor1 interface implementation

    This is intended to be subclassed with a concrete implementation.
    """

    def __init__(self, bus, index, uuid, flags, characteristic):
        self.path = characteristic.path + '/desc' + str(index)
        super().__init__(bus, self.path)
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.characteristic = characteristic

    def get_properties(self):
        return {
            GATT_DESCRIPTOR_IFACE: {
                'Characteristic': self.characteristic.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags,
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def _read_value(self, options):
        """
        Called when the remote tries to read this descriptor.
        Should return a dbus byte array.
        """
        logger.warning("Default Descriptor ReadValue called, returning error")
        raise NotSupportedException()

    def _write_value(self, value, options):
        """
        Called when the remote tries to write to this descriptor.
        """
        logger.warning("Default Descriptor WriteValue called, returning error")
        raise NotSupportedException()

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_DESCRIPTOR_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_DESCRIPTOR_IFACE]

    @dbus.service.method(GATT_DESCRIPTOR_IFACE, in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        return self._read_value(options)

    @dbus.service.method(GATT_DESCRIPTOR_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        self._write_value(value, options)


class Advertisement(dbus.service.Object):
    """
    org.bluez.LEAdvertisement1 interface implementation
    """

    #: base of the path to this D-Bus object (can be overwritten)
    PATH_BASE = '/org/bluez/bluenet/advertisement'

    def __init__(self, bus, index, advertising_type):
        self.path = self.PATH_BASE + str(index)
        super().__init__(bus, self.path)
        self.bus = bus
        self.ad_type = advertising_type
        self.service_uuids = None
        self.manufacturer_data = None
        self.solicit_uuids = None
        self.service_data = None
        self.include_tx_power = False

    def get_properties(self):
        properties = dict()
        properties['Type'] = self.ad_type
        if self.service_uuids is not None:
            properties['ServiceUUIDs'] = dbus.Array(self.service_uuids, signature='s')
        if self.solicit_uuids is not None:
            properties['SolicitUUIDs'] = dbus.Array(self.solicit_uuids, signature='s')
        if self.manufacturer_data is not None:
            properties['ManufacturerData'] = dbus.Dictionary(self.manufacturer_data, signature='qv')
        if self.service_data is not None:
            properties['ServiceData'] = dbus.Dictionary(self.service_data, signature='sv')
        if self.include_tx_power is not None:
            properties['IncludeTxPower'] = dbus.Boolean(self.include_tx_power)
        return {LE_ADVERTISEMENT_IFACE: properties}

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service_uuid(self, uuid):
        if not self.service_uuids:
            self.service_uuids = []
        self.service_uuids.append(uuid)

    def add_solicit_uuid(self, uuid):
        if not self.solicit_uuids:
            self.solicit_uuids = []
        self.solicit_uuids.append(uuid)

    def add_manufacturer_data(self, manuf_code, data):
        if not self.manufacturer_data:
            self.manufacturer_data = dbus.Dictionary({}, signature='qv')
        self.manufacturer_data[manuf_code] = dbus.Array(data, signature='y')

    def add_service_data(self, uuid, data):
        if not self.service_data:
            self.service_data = dbus.Dictionary({}, signature='sv')
        self.service_data[uuid] = dbus.Array(data, signature='y')

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != LE_ADVERTISEMENT_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[LE_ADVERTISEMENT_IFACE]

    @dbus.service.method(LE_ADVERTISEMENT_IFACE, in_signature='', out_signature='')
    def Release(self):
        logger.info("%s: Released!" % self.path)


class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.freedesktop.DBus.Error.InvalidArgs'


class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotSupported'


class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotPermitted'


class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.InvalidValueLength'


class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.Failed'


def string_to_dbus_array(value):
    return [dbus.Byte(c) for c in value.encode()]
