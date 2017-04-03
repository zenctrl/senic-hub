import logging

from functools import partial
from pprint import pformat

from nuimo import (Controller, ControllerListener, ControllerManager, Gesture)

from . import errors, icons

from .hass import HomeAssistant
from .led import LEDMatrixConfig


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
        raise errors.NuimoControllerConnectionError

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

        self.rotation_value = 0
        self.action_in_progress = None

        self.ha = HomeAssistant(ha_api_url, on_connect=self.ha_connected)

    def run(self):
        self.ha.start()
        self.manager.run()

    def stop(self):
        self.ha.stop()
        self.manager.stop()

    def ha_connected(self):
        self.controller.listener = self

        for component in self.components:
            self.initialize_component(component)

    def initialize_component(self, component):
        logger.debug("Initializing component: %s", component.name)

        def set_state(state):
            if not state:
                # Couldn't retrieve state for the component. Most
                # probably entity_id doesn't exist in Home Assistant.
                return

            component.set_state(state)
            logger.debug("Setting state for component %s:", component.name)
            logger.debug(pformat(state))

            # register a state_changed callback that is called
            # every time there's a state changed event for any of
            # entities known by the component
            self.ha.register_state_listener(component.entity_id, component.state_changed)

            # set active component if it's not set already
            if not self.active_component:
                self.set_active_component()

        self.ha.get_state(component.entity_id, [set_state], self.show_error_icon)

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
            self.show_error_icon()
            return

        if event.gesture == Gesture.ROTATION:
            action = self.process_rotation(event.value)
        else:
            action = self.process_gesture(event.gesture)

        if action:
            self.execute_action(action)

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

    def process_rotation(self, rotation_value):
        self.rotation_value += rotation_value

        if not self.action_in_progress:
            action = self.active_component.rotation(self.rotation_value)
            self.rotation_value = 0
            self.action_in_progress = action
            return action

    def process_gesture(self, gesture):
        action = None

        if gesture == Gesture.BUTTON_PRESS:
            action = self.active_component.button_press()

        elif gesture == Gesture.SWIPE_LEFT:
            action = self.active_component.swipe_left()

        elif gesture == Gesture.SWIPE_RIGHT:
            action = self.active_component.swipe_right()

        else:
            # TODO handle all remaining gestures...
            pass

        return action

    def execute_action(self, action):
        def call_service_callback(entity_id, response):
            if response["success"]:
                matrix_config = action.led_matrix_config
            else:
                matrix_config = LEDMatrixConfig(icons.ERROR)

            self.update_led_matrix(matrix_config)

            self.action_in_progress = None

        attributes = {"entity_id": action.entity_id}
        attributes.update(action.extra_args)

        callback = partial(call_service_callback, action.entity_id)
        self.ha.call_service(action.domain, action.service, attributes, callback, self.show_error_icon)

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
            logger.debug("active component: %s", active_component.name)

            if self.active_component:
                self.ha.unregister_state_listener(self.active_component.entity_id)

            self.active_component = active_component
            self.ha.register_state_listener(self.active_component.entity_id, self.state_changed)

            if self.controller.is_connected():
                self.show_active_component()

    def state_changed(self, state):
        """
        Gets called whenever state changes in any device within
        currently active component group.

        """

    def show_active_component(self):
        if self.active_component:
            index = self.components.index(self.active_component)
            icon = icons.icon_with_index(self.active_component.ICON, index)
        else:
            icon = icons.ERROR

        self.update_led_matrix(LEDMatrixConfig(icon))

    def show_error_icon(self):
        self.update_led_matrix(LEDMatrixConfig(icons.ERROR))

    def update_led_matrix(self, matrix_config):
        self.controller.display_matrix(
            matrix_config.matrix,
            fading=matrix_config.fading,
            ignore_duplicates=matrix_config.ignore_duplicates,
        )

    def quit(self):
        if self.controller.is_connected():
            self.controller.disconnect()
