import logging

from time import sleep, time

from lightify import Lightify

from . import ThreadComponent, clamp_value
from .. import matrices


logger = logging.getLogger(__name__)


class Component(ThreadComponent):
    MATRIX = matrices.LIGHT_BULB
    TRANSITION_TIME = 2
    MAX_BRIGHTNESS = 100
    MIN_BRIGHTNESS = 0

    def __init__(self, component_id, config):
        super().__init__(component_id, config)

        self.gateway = Lightify(config['ip_address'])
        self.light = None
        self.on = None
        self.prev_on = None
        self.brightness = None
        self.brightness_delta = 0

    def on_button_press(self):
        self.on = not self.on

        if self.on:
            if self.brightness <= self.MIN_BRIGHTNESS:
                self.brightness = self.MAX_BRIGHTNESS

    def on_rotation(self, delta):
        self.brightness_delta += delta

    def send_updates(self):

        if self.brightness_delta != 0:
            if not self.on:
                self.brightness = self.MIN_BRIGHTNESS

            new_brightness = round(clamp_value(self.brightness + self.brightness_delta * self.MAX_BRIGHTNESS, range(self.MIN_BRIGHTNESS, self.MAX_BRIGHTNESS)))
            if new_brightness == self.brightness:
                return

            self.brightness = new_brightness

            logger.debug("new brightness is: %s", self.brightness)
            self.light.set_luminance(self.brightness, self.TRANSITION_TIME)
            if self.brightness > self.MIN_BRIGHTNESS:
                self.on = True
                matrix = matrices.progress_bar(self.brightness / self.MAX_BRIGHTNESS)
                self.nuimo.display_matrix(matrix, fading=True, ignore_duplicates=True)
            else:
                self.on = False
                self.nuimo.display_matrix(matrices.LIGHT_OFF)
        else:
            if self.on:
                self.light.set_luminance(self.brightness, self.TRANSITION_TIME)
                self.nuimo.display_matrix(matrices.LIGHT_ON)
                logger.debug("light is on, brightness is: %s", self.brightness)
            else:
                self.light.set_luminance(self.MIN_BRIGHTNESS, self.TRANSITION_TIME)
                self.nuimo.display_matrix(matrices.LIGHT_OFF)
                logger.debug("light is off, brightness is: %s", self.brightness)

    def run(self):
        self.update_state()

        prev_sync_time = time()
        prev_update_time = time()

        while not self.stopped:
            now = time()

            if (self.brightness_delta != 0 or self.on != self.prev_on) and now - prev_update_time >= 0.1:
                self.send_updates()
                self.brightness_delta = 0
                self.prev_on = self.on

                prev_update_time = now

            if now - max([prev_sync_time, prev_update_time]) >= 3:
                self.update_state()

                prev_sync_time = now

            sleep(0.05)

    def update_state(self):
        self.gateway.update_all_light_status()
        self.light = list(self.gateway.lights().values())[0]
        self.on = self.light.on()
        self.prev_on = self.on
        if self.light.lum() > self.MIN_BRIGHTNESS:
            self.brightness = self.light.lum()
