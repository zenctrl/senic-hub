import logging

from importlib import import_module
from threading import Thread
import time

import ctypes
import mmap
import os
import struct

from nuimo import (Controller, ControllerListener, ControllerManager, Gesture, LedMatrix)

from . import matrices

import multiprocessing_logging
multiprocessing_logging.install_mp_handler()


logger = logging.getLogger(__name__)


class NuimoControllerListener(ControllerListener):

    is_app_disconnection = False
    connection_failed = False

    def started_connecting(self):
        mac = self.controller.mac_address
        logger.info("Connecting to Nuimo controller %s...", mac)

    def connect_succeeded(self):
        mac = self.controller.mac_address
        self.connection_failed = False
        logger.info("Connected to Nuimo controller %s", mac)

    def connect_failed(self, error):
        mac = self.controller.mac_address
        self.connection_failed = True
        logger.critical("Connection failed %s: %s", mac, error)
        logger.critical("Trying to reconnect to %s", mac)
        self.controller.connect()

    def disconnect_succeeded(self):
        mac = self.controller.mac_address
        logger.warn("Disconnected from %s, reconnecting...", mac)
        if not self.is_app_disconnection:
            self.controller.connect()

    def services_resolved(self):
        mac = self.controller.mac_address
        logger.info("Received services resolved to Nuimo controller %s", mac)

    def received_gesture_event(self, event):
        mac = self.controller.mac_address
        logger.info("Received gesture event to Nuimo controller %s", mac)
        self.process_gesture_event(event)


class NuimoApp(NuimoControllerListener):
    TOUCH_GESTURES = [
        Gesture.TOUCH_LEFT,
        Gesture.TOUCH_RIGHT,
        Gesture.TOUCH_BOTTOM,
    ]

    INTERNAL_GESTURES = [
        Gesture.SWIPE_UP,
        Gesture.SWIPE_DOWN,
    ] + TOUCH_GESTURES

    GESTURES_TO_IGNORE = [
        Gesture.BUTTON_RELEASE,
    ]

    def __init__(self, ha_api_url, ble_adapter_name, mac_address, components):
        super().__init__()

        logger.debug("Initialising NuimoApp for %s" % mac_address)
        self.components = []
        self.active_component = None
        component_instances = get_component_instances(components, mac_address)
        self.set_components(component_instances)
        logger.info("Components associated with this Nuimo: %s" % components)

        self.manager = None
        self.ble_adapter_name = ble_adapter_name
        self.controller = None
        self.mac_address = mac_address
        self.battery_level = None

        # memory map using mmap to store nuimo battery level
        fd = os.open('/tmp/' + self.mac_address.replace(':', '-'), os.O_CREAT | os.O_TRUNC | os.O_RDWR)
        assert os.write(fd, b'\x00' * mmap.PAGESIZE) == mmap.PAGESIZE
        buf = mmap.mmap(fd, mmap.PAGESIZE, mmap.MAP_SHARED, mmap.PROT_WRITE)
        self.bl = ctypes.c_int.from_buffer(buf)
        self.bl.value = 0
        offset = struct.calcsize(self.bl._type_)
        assert buf[offset] == 0

    def set_components(self, components):
        previously_active = self.active_component
        if self.active_component:
            self.active_component.stop()
            self.active_component = None

        for component in components:
            component.nuimo = self
        self.components = components

        if previously_active:
            for component in components:
                if previously_active.component_id == component.component_id:
                    self.set_active_component(component)
                    break

        if self.active_component is None:
            self.set_active_component()

    def start(self, ipc_queue):

        logger.debug("Started a dedicated nuimo control process for %s" %
                     self.mac_address)

        ipc_thread = Thread(target=self.listen_to_ipc_queue,
                            args=(ipc_queue,),
                            name="ipc_thread",
                            daemon=True)
        ipc_thread.start()

        logger.debug("Using adapter (self.ble_adapter_name): %s" % self.ble_adapter_name)
        import subprocess
        output = subprocess.check_output("hciconfig")
        logger.debug("Adapter (from hciconfig): %s " % str(output.split()[0]))

        self.manager = ControllerManager(self.ble_adapter_name)
        self.manager.is_adapter_powered = True
        logger.debug("Powering on BT adapter")

        devices_known_to_bt_module = [device.mac_address for device in self.manager.devices()]
        if self.mac_address not in devices_known_to_bt_module:
            # The Nuimo needs to had been discovered by the bt module
            # at some point before we can do:
            #    self.controller = Controller(self.mac_address, self.manager)
            #
            # and expect it to connect succesfully. If it isn't present
            # discovery needs to be redone until the Nuimo reapears.
            logger.debug("%s not in discovered devices of the bt module. Starting discovery" % self.mac_address)
            self.manager.start_discovery()
            while self.mac_address not in devices_known_to_bt_module:
                time.sleep(3)
                devices_known_to_bt_module = [device.mac_address for device in self.manager.devices()]
                logger.debug("Still haven't found %s" % self.mac_address)
            logger.debug("Found it. Stopping discovery")
            self.manager.stop_discovery()

        self.controller = Controller(self.mac_address, self.manager)
        self.controller.listener = self
        self.set_active_component()
        logger.info("Connecting to Nuimo controller %s", self.controller.mac_address)
        self.controller.connect()
        try:
            self.manager.run()
        except KeyboardInterrupt:
            logger.info("Nuimo app received SIGINT %s", self.controller.mac_address)
            self.stop()

    def stop(self):
        logger.info("Stopping nuimo app of %s ...", self.controller.mac_address)
        if self.active_component:
            self.active_component.stop()

        self.controller.disconnect()
        self.is_app_disconnection = True
        logger.info("Disconnected from Nuimo controller %s", self.controller.mac_address)
        self.manager.stop()
        logger.debug("self manager stop %s", self.controller.mac_address)

    def process_gesture_event(self, event):
        if event.gesture in self.GESTURES_TO_IGNORE:
            logger.debug("Ignoring gesture event: %s", event)
            return

        logger.debug("Processing gesture event: %s", event)

        if event.gesture in self.INTERNAL_GESTURES:
            self.process_internal_gesture(event.gesture)
            return

        if event.gesture == Gesture.BATTERY_LEVEL:
            logger.info("gesture BATTERY LEVEL %d", event.value)
            self.battery_level = event.value
            self.update_battery_level()
            return

        if not self.active_component:
            logger.warn("Ignoring event, no active component")
            self.show_error_matrix()
            return

        if self.active_component.stopped:
            logger.warn("Ignoring event, component is not running")
            self.show_error_matrix()
            return

        if self.active_component.ip_address is not None:
            self.process_gesture(event.gesture, event.value)
            return

        # Process gestures for devices having no IP address in nuimo_app.cfg
        self.process_gesture_event(event.gesture, event.value)

    def process_internal_gesture(self, gesture):
        if gesture == Gesture.SWIPE_UP:
            component = self.get_prev_component()
            if component:
                self.set_active_component(component)

        elif gesture == Gesture.SWIPE_DOWN:
            component = self.get_next_component()
            if component:
                self.set_active_component(component)

        elif gesture in self.TOUCH_GESTURES:
            # Fall-through to show active component...
            pass

        self.show_active_component()

    def process_gesture(self, gesture, delta):
        if gesture == Gesture.ROTATION:
            self.active_component.on_rotation(delta / 1800)  # 1800 is the amount of all ticks for a full ring rotation

        if gesture == Gesture.BUTTON_PRESS:
            self.active_component.on_button_press()

        elif gesture == Gesture.SWIPE_LEFT:
            self.active_component.on_swipe_left()

        elif gesture == Gesture.SWIPE_RIGHT:
            self.active_component.on_swipe_right()

        elif gesture == Gesture.LONGTOUCH_LEFT:
            self.active_component.on_longtouch_left()

        elif gesture == Gesture.LONGTOUCH_BOTTOM:
            self.active_component.on_longtouch_bottom()

        elif gesture == Gesture.LONGTOUCH_RIGHT:
            self.active_component.on_longtouch_right()

        else:
            # TODO handle all remaining gestures...
            pass

    def get_prev_component(self):
        if not self.components:
            return None

        if self.active_component:
            index = self.components.index(self.active_component)
            return self.components[index - 1]
        else:
            return self.components[0]

    def get_next_component(self):
        if not self.components:
            return None

        if self.active_component:
            index = self.components.index(self.active_component)
            try:
                return self.components[index + 1]
            except IndexError:
                return self.components[0]
        else:
            return self.components[0]

    def set_active_component(self, component=None):
        active_component = None

        if component:
            active_component = component
        elif self.components:
            active_component = self.components[0]

        if active_component:
            if self.active_component:
                logger.debug("Stopping component: %s", self.active_component.component_id)
                self.active_component.stop()

            logger.debug("Activating component: %s", active_component.component_id)
            self.active_component = active_component
            self.active_component.start()

    def show_active_component(self):
        if self.active_component:
            index = self.components.index(self.active_component)
            matrix = matrices.matrix_with_index(self.active_component.MATRIX, index)
        else:
            matrix = matrices.ERROR

        self.display_matrix(matrix)

    def show_error_matrix(self):
        self.display_matrix(matrices.ERROR)

    def display_matrix(self, matrix, **kwargs):
        self.controller.display_matrix(LedMatrix(matrix), **kwargs)

    def listen_to_ipc_queue(self, ipc_queue):
        """
        Checks an inter-process queue for new messages. The messages have a simple custom format
        containing the name of one of the defined methods to call and in some cases additional arguments.

        This is required because this NuimoApp instance is executed in its own process (because gatt-python
        doesn't handle multiple devices in a single thread correctly) and it needs to be notified of changes
        and when to quit.
        """

        logger.debug("Started the ipc_queue listener")

        while True:
            msg = ipc_queue.get()
            if msg['method'] == 'set_components':
                components = msg['components']
                logger.info("IPC set_components() received: %s mac = %s", components, self.controller.mac_address)
                component_instances = get_component_instances(components, self.controller.mac_address)
                self.set_components(component_instances)
            elif msg['method'] == 'stop':
                logger.info("IPC stop() received %s", self.controller.mac_address)
                self.stop()
                return

    def update_battery_level(self):
        self.bl.value = self.battery_level


def get_component_instances(components, mac_address):
    """
    Import component modules configured in the Nuimo app configuration
    and return instances of the contained component classes.
    """
    module_name_format = __name__ + '.components.{}'

    instances = []
    first = True
    for component in components:
        module_name = module_name_format.format(component['type'])
        # TODO: philips hue related fix for delete groups - would be better to keep separation of concerns
        component['nuimo_mac_address'] = mac_address
        if component['type'] == 'philips_hue' and first is True:
            component['first'] = True
            first = False
        else:
            component['first'] = False

        # join Sonos speakers
        join = component.get('join', None)
        if join and join['master'] is False:
            continue
        logger.info("Importing module %s", module_name)
        # FIXME: don't ignore errors, this is just a workaround!
        try:
            component_module = import_module(module_name)
            instances.append(component_module.Component(component))
        except Exception as e:
            logger.error("Error during import: %s", e)

    return instances
