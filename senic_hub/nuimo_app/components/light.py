import logging
from pprint import pformat
from time import time
from . import HomeAssistantComponent
from .. import matrices


logger = logging.getLogger(__name__)


class Component(HomeAssistantComponent):
    MATRIX = matrices.LIGHT_BULB
    BRIGHTNESS_CHANGE_RESPONSE_TIMEOUT = 5.0

    def __init__(self, component_id, config):
        super().__init__("light", component_id, config)

        self.brightness = None
        self.is_brightness_request_pending = False
        self.last_brightness_request_time = 0
        self.should_send_brightness_again = False

    def update_from_ha_state(self, state):
        super().update_from_ha_state(state)
        logger.debug("Updated light state: %s", pformat(state))
        if self.is_on:
            received_brightness = state.get('attributes', {}).get('brightness', None)
        else:
            received_brightness = None
        if received_brightness is not None:
            # Only overwrite our brightness if we haven't recently modified it ourselves
            # This avoids synching with an old brightness while the user is still turning the wheel
            if self.brightness is None or time() - self.last_brightness_request_time > Component.BRIGHTNESS_CHANGE_RESPONSE_TIMEOUT:
                self.brightness = received_brightness
        else:
            self.brightness = None
        logger.debug("Is On: %s, Brightness: %s", self.is_on, self.brightness)

    def on_rotation(self, delta):
        if (not self.is_on or (self.brightness or 0) <= 0) and delta <= 0:
            self.nuimo.display_matrix(matrices.LIGHT_OFF)
            return
        if self.brightness is None:
            self.brightness = 1
        else:
            self.brightness = min(max(int(self.brightness + 255 * delta), 0), 255)
        if self.brightness == 0:
            self.turn_off()
        else:
            self.send_brightness()
        self.nuimo.display_matrix(matrices.progress_bar(self.brightness / 255.0), fading=True, ignore_duplicates=True)

    def on_button_press(self):
        # TODO: When triggering play state change, we won't know very soon which new state the player is in.
        #       This said, when the user continuosly presses the button we can't quickly switch playback state yet.
        if self.is_on is None:
            self.nuimo.display_matrix(matrices.ERROR)
        elif self.is_on:
            self.turn_off()
        else:
            self.turn_on()

    def turn_on(self):
        self.nuimo.display_matrix(matrices.LIGHT_ON)
        self.call_ha_service("turn_on")

    def turn_off(self):
        self.nuimo.display_matrix(matrices.LIGHT_OFF)
        self.call_ha_service("turn_off")

    def on_swipe_right(self):
        logger.debug("swipe right")

    def on_swipe_left(self):
        logger.debug("swipe left")

    def send_brightness(self):
        if (self.is_brightness_request_pending and
                (time() - self.last_brightness_request_time < Component.BRIGHTNESS_CHANGE_RESPONSE_TIMEOUT)):
            logger.debug("Delay brightness sending, previous brightness service call still in progress")
            self.should_send_brightness_again = True
            return

        logger.debug("Make brightness service call with brightness %s", self.brightness)

        def on_success(result):
            logger.debug("Brightness service call succeeded")
            self.is_brightness_request_pending = False
            if self.should_send_brightness_again:
                self.should_send_brightness_again = False
                logger.debug("Make brightness service call again since Nuimo's wheel has been rotated in the meanwhile")
                self.send_brightness()

        def on_error():
            logger.debug("Brightness service call failed")
            self.is_brightness_request_pending = False

        self.is_brightness_request_pending = True
        self.last_brightness_request_time = time()
        self.call_ha_service("turn_on", {"brightness": self.brightness}, on_success, on_error)
