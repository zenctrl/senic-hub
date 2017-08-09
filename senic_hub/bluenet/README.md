**Documentation for [BlueZ GATT Peripheral Library for Python](https://github.com/luminosuslight/senic-hub/tree/bluenet-docs/senic_hub/bluenet#bluez-gatt-peripheral-library-for-python) is below.**

# Bluenet - Daemon for Bluetooth LE based Wifi Provisioning

This daemon can be used to provision the Wifi connection of an IoT device via Bluetooth Low Energy.
It creates a BLE GATT service with characteristics to get a list of available networks and to submit the SSID of the network to connect to and the credentials for it.

## GATT Profile

The following GATT profile is provided by Bluenet for a setup app:

* Service:
    * UUID: `FBE51523-B3E6-4F68-B6DA-410C0BBA1A78`
    * This service is advertised by Bluenet and contains all the characteristics below.
* Available Networks:
    * UUID: `FBE51524-B3E6-4F68-B6DA-410C0BBA1A78`
    * GATT characteristic sending a list of network names.
    * Possible operations: Notify
    * Sends one SSID at a time with each notify signal.
    * After all SSIDs have been sent it waits for 3s and starts from begin.
* Connection State:
    * UUID: `FBE51525-B3E6-4F68-B6DA-410C0BBA1A78`
    * GATT characteristic sending the current Wifi connection status.
    * Possible operations: Read + Notify
    * First byte  is the connection status (0: Down 1: Disconnected, 2: Connecting, 3: Connected)
    * In case of Connecting or Connected the remaining bytes are the currently used SSID.
* Hostname:
    * UUID: `FBE51526-B3E6-4F68-B6DA-410C0BBA1A78`
    * GATT characteristic providing the host name of the server.
    * Possible operations: Read + Notify
    * Content: host name as array of characters
* Version:
    * UUID: `FBE51527-B3E6-4F68-B6DA-410C0BBA1A78`
    * GATT characteristic providing the version of this GATT service.
    * Possible operations: Read
    * Content: Version as a string (array of characters)
* SSID:
    * UUID: `FBE51528-B3E6-4F68-B6DA-410C0BBA1A78`
    * GATT characteristic for setting the SSID to connect with.
    * An attempt to join the network is made when the credentials are received.
    * Possible operations: Write
    * Content: SSID as array of characters
* Credentials:
    * UUID: `FBE51529-B3E6-4F68-B6DA-410C0BBA1A78`
    * GATT characteristic for providing the credentials needed to join a network.
    * When this characteristic is written an attempt is made to join the specified network.
    * Possible operations: Write
    * Content: Credentials (i.e. Wifi password) as array of characters

## Prerequisites

Bluenet requires [Python 3.4+](https://www.python.org). Currently Linux is the only supported operating system and therefore it needs a recent installation of [BlueZ](http://www.bluez.org/). It is tested to work fine with BlueZ 5.44.
[NetworkManager 1.8+](https://wiki.gnome.org/Projects/NetworkManager) and [python-networkmanager 2.0.2+](https://pypi.python.org/pypi/python-networkmanager) (there is a bug in 2.0.1) is required in order to scan and join Wifi networks.

## Installation

See [gatt-python](https://github.com/getsenic/gatt-python) on how to install BlueZ.

NetworkManager can be either installed from source or with the packet manager of your choice.
The required python modules can be installed with `pip3 install python-networkmanager dbus-python click`.
The GObject bindings for Python 3 also have to be installed (i.e. `sudo apt-get install python3-gi`).


**Important**: in the current release of python-networkmanager (2.0.1) is a show stopper bug (it is already fixed upstream [here](https://github.com/seveas/python-networkmanager/commit/aea55e82cfd888e12bb4cd7b7c4fffba1a6c09ba)).

It can be fixed manually by changing line 209 in `NetworkManager.py` to:
```        code += "    SignalDispatcher.add_signal_receiver('%s', '%s', self, func, list(args), kwargs)"  % (interface, name)```
(changing `args` -> `list(args)`)

## Usage

Bluenet can be started for example with the following command:

```python3 bluenet.py -w wlan0 -b hci0 start -h your.dns.name -a Devicename```

See `python3 bluenet.py --help` for more information about the commands.

The connection that Bluenet creates in NetworkManager when trying to join a Wifi network is named `bluenet`.

Bluenet may need superuser rights to access the D-Bus API of BlueZ and NetworkManager, if not configured otherwise. It also needs root rights to disable BR/EDR (see Known Issues).

## Known Issues

Android 5.1 tries to connect to BlueZ with BR/EDR instead of Bluetooth Low Energy by default. It then cannot see the service or interact with the characteristics.

This is a problem in BlueZ and the workaround implemented in Bluenet is to disable BR/EDR for the used bluetooth adapter. This can be a **problem if BR/EDR is required for something else** and **superuser rights are required for it**.


Bluenet doesn't support other authentication methods beside WPA(2) and open networks.

## Contributing

Contributions are welcome via pull requests. Please open an issue first in case you want to discuss your possible improvements to this library.

## License

Bluenet is available under the MIT License.

---

# BlueZ GATT Peripheral Library for Python

Bluetooth Low Energy devices can either act as a *Central* or *Peripheral* device. The peripheral is the device that has information to share and the central consumes it. Typically the central device is a smartphone or tablet and the peripheral is for example a fitness tracker.

This library is a Python wrapper above the D-Bus interface of BlueZ and can be used to create a peripheral device.

## Prerequisites

This library requires [Python 3.4+](https://www.python.org). Currently Linux is the only supported operating system and therefore it needs a recent installation of [BlueZ](http://www.bluez.org/). It works only with BlueZ 5.44+ and requires the **experimental features of BlueZ** to be enabled. [Here you can find information on how to enable them.](https://learn.adafruit.com/install-bluez-on-the-raspberry-pi/installation#enable-bluetooth-low-energy-features)

In addition `dbus-python` is required and can be installed with `pip3 install dbus-python`.

Make sure the access rights for the D-Bus interface of BlueZ are configured right, if not, superuser rights may be required.

## Usage

In order to create a custom BLE peripheral device you need to create a GATT service by subclassing the interfaces in `dbus_bluez_interfaces.py` and then register them with BlueZ. The *Peripheral* class in `bluez_peripheral.py`can be used to do so and to start a main loop that is required for this to work.

An example implementation of a GATT service can be found in `bluenet_gatt_service.py`. It is used in `bluenet.py` to create a daemon for Bluetooth based Wifi provisioning.

## Contributing

Contributions are welcome via pull requests. Please open an issue first in case you want to discuss your possible improvements to this library.

## License

The *BlueZ GATT Peripheral Library for Python* is available under the MIT License.