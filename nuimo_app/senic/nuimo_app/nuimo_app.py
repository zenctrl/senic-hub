import logging

from functools import partial
from pprint import pformat

from nuimo import (Controller, ControllerListener, Gesture)

from .import errors, icons
from .led import LEDMatrixConfig


logger = logging.getLogger(__name__)


class NuimoControllerListener(ControllerListener):
    def started_connecting(self):
        mac = self.controller.mac_address
        logger.info("Connecting to Nuimo controller %s...", mac)

    def connect_succeeded(self):
        mac = self.controller.mac_address
        logger.info("Connected to Nuimo controller %s", mac)
        if self.active_component:
            self.show_active_component()
        else:
            if self.components:
                self.set_active_component()

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

    def __init__(self, ha_api, mac_address, manager):
        super().__init__()

        self.components = []
        self.active_component = None

        self.controller = Controller(mac_address, manager)
        self.controller.listener = self
        self.controller.connect()

        self.rotation_value = 0
        self.action_in_progress = None

        self.ha = ha_api

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
            logger.debug("service_call response for %s:", entity_id)
            logger.debug(pformat(response))

            status = response["success"]
            action.entity_updated(entity_id, status)

            # check if action has been already applied to all entities
            if action.is_complete():
                if action.is_successful():
                    matrix_config = action.led_matrix_config
                else:
                    matrix_config = LEDMatrixConfig(icons.ERROR)

                self.update_led_matrix(matrix_config)

                self.action_in_progress = None

        for entity_id in action.entity_ids:
            attributes = {"entity_id": entity_id}
            attributes.update(action.extra_args)

            callback = partial(call_service_callback, entity_id)
            self.ha.call_service(action.domain, action.service, attributes, callback)

    def register_component(self, component):
        def set_state(state):
            component.set_state(state)
            self.components.append(component)
            logger.debug("New component registered: %s initial state:", component.name)
            logger.debug(pformat(state))

            # register a state_changed callback that is called
            # every time there's a state changed event for any of
            # entities known by the component
            self.ha.register_state_listener(component.entity_ids, component.state_changed)

            # show active component if we can
            if not self.active_component and self.components:
                self.set_active_component()

        self.ha.get_state(component.entity_ids, set_state)

    def get_prev_component(self):
        if not self.components:
            return None

        if self.active_component:
            index = self.components.index(self.active_component)
            return self.components[index-1]
        else:
            return self.components[0]

    def get_next_component(self):
        if not self.components:
            return None

        if self.active_component:
            index = self.components.index(self.active_component)
            try:
                return self.components[index+1]
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
                self.ha.unregister_state_listener(self.active_component.entity_ids)

            self.active_component = active_component
            self.ha.register_state_listener(self.active_component.entity_ids, self.state_changed)

            if self.controller.is_connected():
                self.show_active_component()

    def state_changed(self, state):
        """
        Gets called whenever state changes in any device within
        currently active component group.

        """
        logger.debug("state_changed:")
        logger.debug(pformat(state))

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
