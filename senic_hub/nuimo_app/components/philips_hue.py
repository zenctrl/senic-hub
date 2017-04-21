import logging

from random import random, seed
from time import sleep, time

from phue import Bridge, PhueRequestTimeout

from . import BaseComponent, EncoderRing

from .. import matrices


COLOR_WHITE_XY = (0.32, 0.336)
SENIC_HUB_GROUP_NAME = "Senic hub demo"


logger = logging.getLogger(__name__)


class Component(BaseComponent):
    MATRIX = matrices.LIGHT_BULB

    # don't send updates to the bridge more often than UPDATE_INTARVAL
    UPDATE_INTERVAL = 0.1  # seconds

    # how often to sync with the bridge to detect changes made by external apps
    SYNC_INTERVAL = 5  # seconds

    def __init__(self, config):
        super().__init__(config)

        self.encoder = EncoderRing(1, 254)

        self.bridge = Bridge(config['ip_address'], config['username'])
        self.entity_id = self.get_or_create_entity()

        self.is_on = None
        self.brightness = None
        self.delta = 0
        self.update_state()

        # seed random nr generator (used to get random color value)
        seed()

    def get_or_create_entity(self):
        """
        Create or update group if there is more than 1 hue bulb
        available, otherwise return ID of the bulb.
        """
        # TODO handle cases when light becomes available later at some point
        lights = {k: v for k, v in self.bridge.get_light().items() if v['state']['reachable']}
        if not lights:
            return None
        elif len(lights) == 1:
            return int(list(lights.keys())[0])

        groups = self.bridge.get_group()
        group_id = next((k for k, v in groups.items() if v['name'] == SENIC_HUB_GROUP_NAME), None)
        if not group_id:
            return self.create_light_group(lights)

        group_lights = set(groups[group_id]['lights'])
        all_lights = set(lights.keys())

        group_id = int(group_id)

        if group_lights != all_lights:
            return self.update_light_group(group_id, lights)

        return group_id

    def create_light_group(self, lights):
        response = self.bridge.create_group(SENIC_HUB_GROUP_NAME, list(lights.keys()))
        return int(response[0]['success']['id'])

    def update_light_group(self, group_id, lights):
        self.bridge.set_group(group_id, 'lights', list(lights.keys()))
        return group_id

    def update_state(self):
        if not self.entity_id:
            return

        try:
            settings = self.bridge.get_light(self.entity_id)

            self.is_on = settings['state']['on']
            self.brightness = settings['state']['bri']
        except (PhueRequestTimeout, ConnectionResetError):
            logger.exception()

    def on_button_press(self):
        on = not self.is_on
        if on and self.brightness:
            self.set_light_attributes(on=on, bri=self.brightness)
        else:
            self.set_light_attributes(on=on)

    def set_light_attributes(self, **attributes):
        if self.entity_id:
            responses = self.bridge.set_light(self.entity_id, attributes, transitiontime=1)
            self.set_state_from_responses(responses, attributes)
        else:
            self.nuimo.display_matrix(matrices.ERROR)

    def set_state_from_responses(self, responses, request_attributes):
        error = any(x for x in responses[0] if 'error' in x)

        if error:
            self.nuimo.display_matrix(matrices.ERROR)
            return

        updates = self.merge_updates(responses)

        for key, value in updates.items():
            if key == 'bri':
                self.brightness = value

                if not self.brightness:
                    self.turn_off()
                    return

            elif key == 'on':
                self.is_on = value

        if 'xy' in updates:
            if 'bri' in request_attributes:
                self.nuimo.display_matrix(matrices.LETTER_W)
            else:
                self.nuimo.display_matrix(matrices.SHUFFLE)

        elif 'bri' in updates:
            matrix = matrices.light_bar(self.encoder.max_value, self.brightness)
            self.nuimo.display_matrix(matrix, fading=True, ignore_duplicates=True)

        elif 'on' in updates:
            if self.is_on:
                matrix = matrices.LIGHT_ON
            else:
                matrix = matrices.LIGHT_OFF

            self.nuimo.display_matrix(matrix)

    def merge_updates(self, responses):
        updates = [x['success'] for x in responses[0] if not list(x['success'])[0].endswith('transitiontime')]
        return {k.rsplit("/", 1)[-1]: v for u in updates for k, v in u.items()}

    def turn_off(self):
        self.set_light_attributes(on=False)

    def on_swipe_left(self):
        # TODO don't set xy for bulbs that don't support color
        self.set_light_attributes(on=True, bri=self.brightness, xy=COLOR_WHITE_XY)

    def on_swipe_right(self):
        # TODO don't set xy for bulbs that don't support color
        self.set_light_attributes(on=True, xy=(random(), random()))

    def on_rotation(self, value):
        self.delta += value

    def run(self):
        prev_sync_time = 0
        self.stopping = False

        while not self.stopping:
            now = time()

            if self.delta and now - prev_sync_time >= self.UPDATE_INTERVAL:
                self.send_updates()
                self.delta = 0

                prev_sync_time = now

            if now - prev_sync_time >= self.SYNC_INTERVAL:
                self.update_state()

                prev_sync_time = now

            sleep(0.05)

    def send_updates(self):
        delta = round(self.encoder.points_to_value(self.delta))

        if self.is_on:
            self.set_light_attributes(bri_inc=delta)
        else:
            if delta > 0:
                self.set_light_attributes(bri_inc=delta, on=True)
