import logging

from nuimo import (Controller, ControllerListener, ControllerManager, Gesture, LedMatrix)

from . import matrices


logger = logging.getLogger(__name__)


class NuimoControllerListener(ControllerListener):

    def started_connecting(self):
        mac = self.controller.mac_address
        logger.info("Connecting to Nuimo controller %s...", mac)

    def connect_succeeded(self):
        mac = self.controller.mac_address
        logger.info("Connected to Nuimo controller %s", mac)

    def connect_failed(self, error):
        mac = self.controller.mac_address
        logger.critical("Connection failed %s: %s", mac, error)
        self.controller.connect()

    def disconnect_succeeded(self):
        mac = self.controller.mac_address
        logger.warn("Disconnected from %s, reconnecting...", mac)
        self.controller.connect()

    def received_gesture_event(self, event):
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

        self.components = components
        self.active_component = None

        self.manager = ControllerManager(ble_adapter_name)

        self.controller = Controller(mac_address, self.manager)
        self.controller.listener = self
        self.controller.connect()

        for component in self.components:
            component.nuimo = self

        component = self.get_next_component()
        if component:
            self.set_active_component(component)

    def start(self):
        self.manager.run()

    def stop(self):
        if self.active_component:
            self.active_component.stop()

        self.controller.disconnect()
        self.manager.stop()

    def process_gesture_event(self, event):
        if event.gesture in self.GESTURES_TO_IGNORE:
            logger.debug("Ignoring gesture event: %s", event)
            return

        logger.debug("Processing gesture event: %s", event)

        if event.gesture in self.INTERNAL_GESTURES:
            self.process_internal_gesture(event.gesture)
            return

        if not self.active_component:
            logger.warn("Ignoring event, no active component...")
            self.show_error_matrix()
            return

        self.process_gesture(event.gesture, event.value)

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
