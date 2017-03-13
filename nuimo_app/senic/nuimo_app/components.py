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

        self.set_state([new_state])

    def make_action(self, service, led_matrix_config, **kw):
        """
        Helper that returns an Action object.

        """
        return Action(self.DOMAIN, service, self.entity_ids, led_matrix_config, **kw)


class PhilipsHue(Component):
    DOMAIN = "light"
    ICON = icons.LIGHT_BULB

    MAX_BRIGHTNESS_VALUE = 255
    MAX_HUE_VALUE = 65535

    STATE_ICONS = {
        "on": icons.LIGHT_ON,
        "off": icons.LIGHT_OFF,
    }

    def __init__(self, name, entities):
        self.name = name

        self.entity_ids = tuple(entities)

        self.state = {}  # entity_id: state
        self.brightness = {}  # entity_id: brightness

        # if any of the lights is off we assume all are off
        self.is_light_on = None

        # seed random nr generator (used to get random color value)
        seed()

    def set_state(self, states):
        """
        Set internal state from the HA state.

        """
        for state in states:
            entity_id = state["entity_id"]

            self.state[entity_id] = state["state"]
            self.brightness[entity_id] = state["attributes"].get("brightness", 0)

            logger.debug(
                "%s state: %s brightness: %s", entity_id, self.state[entity_id],
                self.brightness[entity_id])

        self.is_light_on = all(x == "on" for x in self.state.values())

    def button_press(self):
        """
        Toggle the state of all lights.

        """
        if self.is_light_on:
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

        for entity_id, brightness in self.brightness.items():
            new_value = min([max([0, brightness + delta]), self.MAX_BRIGHTNESS_VALUE])
            logger.debug("%s brightness current: %s delta: %s new: %s", entity_id,
                         brightness, delta, new_value)

            self.brightness[entity_id] = new_value

        max_value = max(self.brightness.values())

        # turn off bulbs if brightness has reached 0
        args = dict(transition=0)
        if max_value > 1:
            service = "turn_on"
            args["brightness"] = max_value
            icon = icons.light_bar(self.MAX_BRIGHTNESS_VALUE, max_value)
        else:
            service = "turn_off"
            icon = icons.POWER_OFF

        led_cfg = LEDMatrixConfig(icon, fading=True, ignore_duplicates=True)
        return self.make_action(service, led_cfg, **args)

    def swipe_left(self):
        led_cfg = LEDMatrixConfig(icons.LETTER_W)
        brightness = max(self.brightness.values())
        return self.make_action("turn_on", led_cfg, rgb_color=COLOR_WHITE_RGB, brightness=brightness)

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

    def __init__(self, name, entities):
        self.name = name

        self.entity_ids = tuple(entities)

        self.state = {}  # entity_id: state
        self.volume = {}  # entity_id: volume

    def set_state(self, states):
        """
        Set internal state from the HA state.

        """
        for state in states:
            entity_id = state["entity_id"]

            self.state[entity_id] = state["state"]
            self.volume[entity_id] = state["attributes"].get("volume_level", 0)

            logger.debug(
                "%s state %s volume: %s", entity_id, self.state[entity_id], self.volume[entity_id])

    def button_press(self):
        """
        Toggle the state of the Sonos speaker.

        NOTE: only works with one speaker currently.

        """
        state = self.state[list(self.state.keys())[0]]

        if state == "playing":
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

        NOTE: only works with one speaker currently.

        """
        entity_id = list(self.volume.keys())[0]
        volume = self.volume[entity_id]

        delta = value / 1800
        new_value = min([max([0, volume + delta]), self.MAX_VOLUME_VALUE])
        logger.debug("volume %s current: %s delta: %s new: %s", entity_id, volume, delta, new_value)

        self.volume[entity_id] = new_value

        icon = icons.light_bar(self.MAX_VOLUME_VALUE, new_value)
        led_cfg = LEDMatrixConfig(icon, fading=True, ignore_duplicates=True)
        return self.make_action("volume_set", led_cfg, volume_level=new_value)

    def swipe_left(self):
        led_cfg = LEDMatrixConfig(icons.PREVIOUS_SONG)
        return self.make_action("media_previous_track", led_cfg)

    def swipe_right(self):
        led_cfg = LEDMatrixConfig(icons.NEXT_SONG)
        return self.make_action("media_next_track", led_cfg)
