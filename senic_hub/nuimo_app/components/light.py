import logging
from pprint import pformat
from time import time
from . import HomeAssistantComponent
from .. import matrices


logger = logging.getLogger(__name__)


class Component(HomeAssistantComponent):
    MATRIX = matrices.LIGHT_BULB

    def __init__(self, config):
        super().__init__("light", config)

    def update_from_ha_state(self, state):
        super().update_from_ha_state(state)
        logger.debug("Updated light state: %s", pformat(state))
        logger.debug("Is On: %s", self.is_on)

    def on_rotation(self, delta):
        logger.debug("rotate")
        pass

    def on_button_press(self):
        # TODO: When triggering play state change, we won't know very soon which new state the player is in.
        #       This said, when the user continuosly presses the button we can't quickly switch playback state yet.
        if self.is_on is None:
            self.nuimo.display_matrix(matrices.ERROR)
        elif self.is_on:
            self.nuimo.display_matrix(matrices.LIGHT_OFF)
            self.call_ha_service("turn_off")
        else:
            self.nuimo.display_matrix(matrices.LIGHT_ON)
            self.call_ha_service("turn_on")

    def on_swipe_right(self):
        logger.debug("swipe right")

    def on_swipe_left(self):
        logger.debug("swipe left")
