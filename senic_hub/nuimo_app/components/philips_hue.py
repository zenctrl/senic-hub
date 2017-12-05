import logging

from pprint import pformat
from time import sleep, time
from random import random
from . import custom_phue_scenes as cps

from phue import Bridge

from . import ThreadComponent, clamp_value

from .. import matrices

import socket


COLOR_WHITE_XY = (0.32, 0.336)


logger = logging.getLogger(__name__)


class HueBase:

    def __init__(self, bridge, light_ids, instance_id, first):
        self.bridge = bridge
        self.light_ids = light_ids
        self.instance_id = instance_id
        self.group_name = "Senic hub " + str(instance_id)
        self.first = first
        logger.debug("self.group_name %s first %s", self.group_name, self.first)

        if len(light_ids) > 1:
            self.group_id = self.get_or_create_group()
        else:
            self.group_id = None

        self._on = None
        self._brightness = None
        self._state = None

    def get_or_create_group(self):
        groups = self.bridge.get_group()

        if self.first:
            for v in groups.items():
                if "Senic hub " in v[1]['name']:
                    if self.instance_id <= int(v[1]['name'].split()[-1]) < self.instance_id + 10:
                        self.delete_group(int(v[0]))

        groups = self.bridge.get_group()

        group_id = next((k for k, v in groups.items() if v['name'] == self.group_name), None)
        if not group_id:
            return self.create_group()

        group_light_ids = set(groups[group_id]['lights'])
        if group_light_ids != set(self.light_ids):
            return self.update_group(int(group_id))

        return int(group_id)

    def create_group(self):
        responses = self.bridge.create_group(self.group_name, self.light_ids)
        logger.debug("create_group responses: %s", responses)
        response = responses[0]
        if 'error' in response:
            logger.error("Error while creating the group: %s", response['error'])
            return None
        return int(response['success']['id'])

    def update_group(self, group_id):
        responses = self.bridge.set_group(group_id, 'lights', self.light_ids)
        logger.debug("update_group responses: %s", responses)
        response = responses[0][0]
        if 'error' in response:
            logger.error("Error while updating the group: %s", response['error'])
            return None

        return group_id

    def delete_group(self, group_id):
        responses = self.bridge.delete_group(group_id)
        logger.debug("delete_group responses: %s", responses)
        response = responses[0]
        if 'error' in response:
            logger.error("Error while updating the group: %s", response['error'])
            return None

        return True

    @property
    def sync_interval(self):
        """
        How often to sync with the bridge to detect changes made by
        external apps.
        """
        return 5  # seconds

    def parse_responses(self, responses, request_attributes):
        errors = [x['error'] for x in responses[0] if 'error' in x]
        if errors:
            return {'errors': errors}

        response = self.merge_success_responses(responses)
        logger.debug("response: %s", response)

        self.update_state_from_response(response)
        return response

    def merge_success_responses(self, responses):
        updates = [x['success'] for x in responses[0] if not list(x['success'])[0].endswith('transitiontime')]
        return {k.rsplit("/", 1)[-1]: v for u in updates for k, v in u.items()}

    def update_state_from_response(self, response):
        for key, value in response.items():
            if key == 'bri':
                self.brightness = value

            elif key == 'on':
                self.on = value

            elif key == 'bri_inc':
                # response to bri_inc applied to a group doesn't return actual brightness for some reason...
                self.brightness = clamp_value(self.brightness + value, range(0, 254))

    @property
    def on(self):
        return self._on

    @on.setter
    def on(self, other):
        self._on = other

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, other):
        self._brightness = other


class EmptyLightSet(HueBase):
    """
    Wrapper used when we don't have any reachable lights to control
    """

    def __init__(self):
        self._on = False
        self._brightness = 0

    @property
    def update_interval(self):
        return 1

    def update_state(self):
        pass

    def set_attributes(self, attributes):
        return {'errors': "No reachable lights"}

    @property
    def sync_interval(self):
        """
        How often to sync with the bridge to detect changes made by
        external apps.
        """
        return 60  # seconds


class LightSet(HueBase):
    """
    Wraps one or multiple lights
    """

    TRANSITION_TIME = 2  # * 100 milliseconds

    @property
    def update_interval(self):
        return 0.1

    def update_state(self):
        """
        Get current state of all the lights from the bridge
        """
        response = self.bridge.get_light()
        self._state = {k: v['state'] for k, v in response.items() if k in self.light_ids}

        logger.debug("state: %s", pformat(self._state))

        self._on = all(s['on'] for s in self._state.values())
        brightness = min(s['bri'] for s in self._state.values())
        if self._on or brightness != 1 or self._brightness is None:
            self._brightness = brightness

        logger.debug("on: %s brightness: %s", self._on, self._brightness)

    def set_attributes(self, attributes):
        # Send ON/OFF  to a group instead lights separately for a nicer UX
        if self.group_id is not None and 'on' in attributes and len(attributes) == 1:
            responses = self.bridge.set_group(self.group_id, attributes, transitiontime=self.TRANSITION_TIME)
            return self.parse_responses(responses, attributes)

        for light_id in self.light_ids:
            responses = self.bridge.set_light(int(light_id), attributes, transitiontime=self.TRANSITION_TIME)
            response = self.parse_responses(responses, attributes)
            if 'errors' in response:
                # exit early if a call fails
                return response

        return response


class Group(HueBase):
    """
    Wraps a Philips Hue group
    """

    TRANSITION_TIME = 2  # * 100 ms

    @property
    def update_interval(self):
        return 1  # second

    def update_state(self):
        """
        Get current state of the group from the bridge
        """
        state = self.bridge.get_group(self.group_id)

        logger.debug("group state: %s", pformat(state))

        self._on = state['state']['all_on']
        if self._on or state['action']['bri'] != 1 or self._brightness is None:
            self._brightness = state['action']['bri']

        self._state = state

    def set_attributes(self, attributes):
        responses = self.bridge.set_group(self.group_id, attributes, transitiontime=self.TRANSITION_TIME)
        return self.parse_responses(responses, attributes)


hue_instances = {}
mac_idx = 0


class Component(ThreadComponent):
    MATRIX = matrices.LIGHT_BULB
    TRANSITION_TIME = 2  # * 100 milliseconds

    def __init__(self, component_config):
        super().__init__(component_config)

        self.bridge = Bridge(component_config['ip_address'], component_config['username'])
        self.id = component_config['id']
        self.group_num = None
        self.scenes = {}
        self.first = component_config['first']

        # TODO: Created groups are not deleted when a Nuimo is removed
        self.nuimo_mac_address = component_config['nuimo_mac_address']

        global hue_instances
        global mac_idx

        if self.first and hue_instances != {} and self.nuimo_mac_address in hue_instances:
            temp = hue_instances[self.nuimo_mac_address]['mac_idx']
            hue_instances[self.nuimo_mac_address] = {}
            hue_instances[self.nuimo_mac_address]['mac_idx'] = temp

        if self.nuimo_mac_address not in hue_instances:
            hue_instances[self.nuimo_mac_address] = {}
            hue_instances[self.nuimo_mac_address]['mac_idx'] = mac_idx
            mac_idx = mac_idx + 1

        if self.id not in hue_instances[self.nuimo_mac_address]:
            hue_instances[self.nuimo_mac_address][self.id] = hue_instances[self.nuimo_mac_address]['mac_idx'] * 10 + len(hue_instances[self.nuimo_mac_address])

        self.group_num = hue_instances[self.nuimo_mac_address][self.id]
        self.delta_range = range(-254, 254)
        self.delta = 0

        # Extract light IDs, they are stored with format `<bridgeID>-light-<lightID>`
        self.light_ids = component_config['device_ids']
        self.light_ids = [i.split('-light-')[1].strip() for i in self.light_ids]

        self.lights = self.create_lights(self.light_ids)
        self.lights.update_state()

        self.station_id_1 = component_config.get('station1', None)
        self.station_id_2 = component_config.get('station2', None)
        self.station_id_3 = component_config.get('station3', None)

        if not any((self.station_id_1, self.station_id_2, self.station_id_3)):
            try:
                self.scenes = self.bridge.get_scene()
            except ConnectionResetError:
                logger.error("Hue Bridge not reachable, handle exception")
            except socket.error as socketerror:
                logger.error("Socket Error: ", socketerror)

            self.scenes = {k: v for k, v in self.scenes.items() if v['lights'] == self.light_ids}

            if len(list(self.scenes.keys())) >= 3:
                for scene in self.scenes:
                    self.station_id_1 = {'name': self.scenes[scene]['name']} if self.scenes[scene]['name'] == 'Nightlight' else self.station_id_1
                    self.station_id_2 = {'name': self.scenes[scene]['name']} if self.scenes[scene]['name'] == 'Relax' else self.station_id_2
                    self.station_id_3 = {'name': self.scenes[scene]['name']} if self.scenes[scene]['name'] == 'Concentrate' else self.station_id_3

    def create_lights(self, light_ids):
        reachable_lights = None
        try:
            reachable_lights = self.filter_reachable(light_ids)
        except ConnectionResetError:
            # TODO: add a library wrapper to handle the issue properly, this is a workaround
            logger.error("Hue Bridge not reachable, handle exception")
        except socket.error as socketerror:
            logger.error("Socket Error: ", socketerror)
        if not reachable_lights:
            lights = EmptyLightSet()
        elif len(reachable_lights) > 10:
            lights = Group(self.bridge, reachable_lights, self.group_num, self.first)
        else:
            lights = LightSet(self.bridge, reachable_lights, self.group_num, self.first)

        return lights

    def filter_reachable(self, light_ids):
        lights = self.bridge.get_light()
        reachable = [i for i in light_ids if i in lights and lights[i]['state']['reachable']]
        logger.debug("lights: %s reachable: %s", list(lights.keys()), reachable)
        return reachable

    def on_button_press(self):
        self.set_light_attributes(on=not self.lights.on, bri=self.lights.brightness)

    def on_longtouch_left(self):
        logger.debug("on_longtouch_left()")
        if self.station_id_1 is not None:
            self.set_station(1, self.station_id_1['name'])
            self.nuimo.display_matrix(matrices.STATION1)

    def on_longtouch_bottom(self):
        logger.debug("on_longtouch_bottom()")
        if self.station_id_2 is not None:
            self.set_station(2, self.station_id_2['name'])
            self.nuimo.display_matrix(matrices.STATION2)

    def on_longtouch_right(self):
        logger.debug("on_longtouch_right()")
        if self.station_id_3 is not None:
            self.set_station(3, self.station_id_3['name'])
            self.nuimo.display_matrix(matrices.STATION3)

    def set_light_attributes(self, **attributes):
        response = self.lights.set_attributes(attributes)

        if 'errors' in response:
            logger.error("Failed to set light attributes: %s", response['errors'])
            if response['errors'][0]['description'] == "parameter, bri, is not modifiable. Device is set to off.":
                pass
            else:
                self.nuimo.display_matrix(matrices.ERROR)
            return

        if 'xy' in attributes:
            if 'bri' in attributes:
                self.nuimo.display_matrix(matrices.LETTER_W)
            else:
                self.nuimo.display_matrix(matrices.SHUFFLE)

        elif 'on' in attributes and not ('bri_inc' in attributes):
            if self.lights.on:
                self.nuimo.display_matrix(matrices.LIGHT_ON)
            else:
                self.nuimo.display_matrix(matrices.LIGHT_OFF)

        elif 'on' in attributes or 'bri_inc' in attributes:
            if self.lights.brightness:
                matrix = matrices.progress_bar(self.lights.brightness / self.delta_range.stop)
                self.nuimo.display_matrix(matrix, fading=True, ignore_duplicates=True)
            else:
                self.set_light_attributes(on=False)

    def on_swipe_left(self):
        self.set_light_attributes(on=True, bri=self.lights.brightness, xy=COLOR_WHITE_XY)

    def on_swipe_right(self):
        self.set_light_attributes(on=True, xy=(random(), random()))

    def on_rotation(self, value):
        self.delta += value

    def run(self):
        prev_sync_time = time()
        prev_update_time = time()

        while not self.stopped:
            now = time()

            if self.delta and now - prev_update_time >= self.lights.update_interval:
                self.send_updates()
                self.delta = 0

                prev_update_time = now

            if now - max([prev_sync_time, prev_update_time]) >= self.lights.sync_interval:
                try:
                    self.lights.update_state()
                except ConnectionResetError:
                    # TODO: add a library wrapper to handle the issue properly, this is a workaround
                    logger.error("connection with Hue Bridge reset by peer, handle exception")
                except socket.error as socketerror:
                    logger.error("Socket Error: ", socketerror)

                prev_sync_time = now

            sleep(0.05)

    def set_station(self, station_number, station_name):
        light_attr = cps.CUSTOM_SCENES['scenes'][station_name]['lightstates']
        logger.info(self.light_ids)

        for l in self.light_ids:
            self.bridge.set_light(int(l), light_attr, transitiontime=self.TRANSITION_TIME)

    def send_updates(self):
        delta = round(clamp_value(self.delta_range.stop * self.delta, self.delta_range))

        if self.lights.on:
            self.set_light_attributes(bri_inc=delta)
        else:
            if delta > 0:
                self.set_light_attributes(on=True)
                self.set_light_attributes(bri_inc=delta)
