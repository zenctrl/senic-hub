import logging

from pprint import pformat
from random import random, seed

from . import icons

from .actions import Action
from .led import LEDMatrixConfig


COLOR_WHITE_RGB = (255, 255, 255)


logger = logging.getLogger(__name__)


class Component:
    def state_changed(self, state):
        """
        Listen on state change notifications from HA.

        This function gets called automatically by HA when state
        changes for one of the entities known to the component.

        """
        logger.debug("state_changed:")
        logger.debug(pformat(state))

        new_state = state["data"]["new_state"]

        self.set_state(new_state)

    def make_action(self, service, led_matrix_config, **kw):
        """
        Helper that returns an Action object.

        """
        return Action(self.DOMAIN, service, self.entity_id, led_matrix_config, **kw)


class PhilipsHue(Component):
    DOMAIN = "light"
    ICON = icons.LIGHT_BULB

    MAX_BRIGHTNESS_VALUE = 255
    MAX_HUE_VALUE = 65535

    STATE_ICONS = {
        "on": icons.LIGHT_ON,
        "off": icons.LIGHT_OFF,
    }

    def __init__(self, name, entity_id):
        self.name = name

        self.entity_id = entity_id

        self.state = None
        self.brightness = None

        # seed random nr generator (used to get random color value)
        seed()

    def set_state(self, state):
        """
        Set internal state from the HA state.

        """
        self.state = state["state"]
        self.brightness = state["attributes"].get("brightness", 0)

        logger.debug("%s state: %s brightness: %s", self.entity_id, self.state, self.brightness)

    def button_press(self):
        """
        Toggle the state of all lights.

        """
        if self.state == "on":
            new_state = "off"
        else:
            new_state = "on"

        service = "turn_{}".format(new_state)
        led_cfg = LEDMatrixConfig(self.STATE_ICONS[new_state])
        return self.make_action(service, led_cfg)

    def rotation(self, value):
        """
        Sets brightness according to the rotation value.

        Philips Hue brightness value is in range from 0 to 255 or
        (1-254 according to official docs) where 0 doesn't mean it's
        off.

        """
        delta = int(value / 1800 * self.MAX_BRIGHTNESS_VALUE)

        new_value = min(max(self.brightness + delta, 0), self.MAX_BRIGHTNESS_VALUE)
        logger.debug("%s brightness current: %s delta: %s new: %s", self.entity_id,
                     self.brightness, delta, new_value)

        self.brightness = new_value

        args = dict(transition=0)
        if new_value:
            service = "turn_on"
            args["brightness"] = new_value
            icon = icons.light_bar(self.MAX_BRIGHTNESS_VALUE, new_value)
        else:
            # turn off bulbs if brightness has reached 0
            service = "turn_off"
            icon = icons.POWER_OFF

        led_cfg = LEDMatrixConfig(icon, fading=True, ignore_duplicates=True)
        return self.make_action(service, led_cfg, **args)

    def swipe_left(self):
        led_cfg = LEDMatrixConfig(icons.LETTER_W)
        return self.make_action("turn_on", led_cfg, rgb_color=COLOR_WHITE_RGB, brightness=self.brightness)

    def swipe_right(self):
        led_cfg = LEDMatrixConfig(icons.SHUFFLE)
        random_xy = [random(), random()]
        return self.make_action("turn_on", led_cfg, xy_color=random_xy)


class Sonos(Component):
    DOMAIN = "media_player"
    ICON = icons.MUSIC_NOTE

    MAX_VOLUME_VALUE = 1

    STATE_ICONS = {
        "playing": icons.PLAY,
        "paused": icons.PAUSE,
    }

    def __init__(self, name, entity_id):
        self.name = name

        self.entity_id = entity_id

        self.state = None
        self.volume = None

    def set_state(self, state):
        """
        Set internal state from the HA state.

        """
        entity_id = state["entity_id"]

        self.state = state["state"]
        self.volume = state["attributes"].get("volume_level", 0)

        logger.debug("%s state %s volume: %s", entity_id, self.state, self.volume)

    def button_press(self):
        if self.state == "playing":
            service = "turn_off"
            new_state = "paused"
        else:
            service = "turn_on"
            new_state = "playing"

        led_cfg = LEDMatrixConfig(self.STATE_ICONS[new_state])
        return self.make_action(service, led_cfg)

    def rotation(self, value):
        """
        Sets value according to the rotation value.

        Sonos volume level value is in the rang from 0.0 to 1.0

        """
        delta = value / 1800
        new_value = min(max(self.volume + delta, 0), self.MAX_VOLUME_VALUE)
        logger.debug("volume %s current: %s delta: %s new: %s", self.entity_id, self.volume, delta, new_value)

        self.volume = new_value

        icon = icons.light_bar(self.MAX_VOLUME_VALUE, new_value)
        led_cfg = LEDMatrixConfig(icon, fading=True, ignore_duplicates=True)
        return self.make_action("volume_set", led_cfg, volume_level=new_value)

    def swipe_left(self):
        led_cfg = LEDMatrixConfig(icons.PREVIOUS_SONG)
        return self.make_action("media_previous_track", led_cfg)

    def swipe_right(self):
        led_cfg = LEDMatrixConfig(icons.NEXT_SONG)
        return self.make_action("media_next_track", led_cfg)
