import logging

from pprint import pformat
from queue import Empty
from time import time

from soco import SoCo, SoCoException
from soco.events import event_listener

from . import ThreadComponent, clamp_value

from .. import matrices


logger = logging.getLogger(__name__)


class Component(ThreadComponent):
    MATRIX = matrices.MUSIC_NOTE

    STATE_PLAYING = 'PLAYING'
    STATE_PAUSED = 'PAUSED_PLAYBACK'
    STATE_STOPPED = 'STOPPED'

    # how many seconds to wait after sending last command before
    # receiving device state change events
    EVENT_IDLE_INTERVAL = 2  # seconds

    def __init__(self, config):
        super().__init__(config)

        self.sonos_controller = SoCo(config['ip_address'])

        self.volume_range = range(0, 100)

        self.event_listener = event_listener  # comes from global scope

        # TODO: Subscribe only when component is active, i.e. "running", unsubscribe when stopped
        self.subscribe_to_events()

        self.state = None
        self.volume = None
        self.update_state()

        self.nuimo = None

        self.stopping = False
        self.last_request_time = time()

    def run(self):
        while not self.stopping:
            try:
                event = self.av_transport_subscription.events.get(timeout=0.1)

                if time() - self.last_request_time > self.EVENT_IDLE_INTERVAL:
                    logger.debug("avTransport event: %s", pformat(event.variables))
                    self.state = event.variables['transport_state']
            except Empty:
                pass

            try:
                event = self.rendering_control_subscription.events.get(timeout=0.1)

                if time() - self.last_request_time > self.EVENT_IDLE_INTERVAL:
                    logger.debug("renderingControl event: %s", pformat(event.variables))
                    self.volume = int(event.variables['volume']['Master'])
            except Empty:
                pass

    def subscribe_to_events(self):
        # TODO: `subscribe` throws if the Speaker is offline
        self.av_transport_subscription = self.sonos_controller.avTransport.subscribe()
        self.rendering_control_subscription = self.sonos_controller.renderingControl.subscribe()

    def update_state(self):
        self.state = self.sonos_controller.get_current_transport_info()['current_transport_state']
        self.volume = self.sonos_controller.volume

        logger.debug("%s state: %s volume: %s", self.sonos_controller.ip_address, self.state, self.volume)

    def on_rotation(self, delta):
        try:
            delta = round(self.volume_range.stop * delta)
            self.volume = clamp_value(self.volume + delta, self.volume_range)
            self.sonos_controller.volume = self.volume

            logger.debug("volume update delta: %s volume: %s", delta, self.volume)

            matrix = matrices.progress_bar(self.volume / self.volume_range.stop)
            self.nuimo.display_matrix(matrix, fading=True, ignore_duplicates=True)

        except SoCoException:
            self.nuimo.display_matrix(matrices.ERROR)

        self.last_request_time = time()

    def on_button_press(self):
        if self.state == self.STATE_PLAYING:
            self.pause()

        elif self.state in [self.STATE_PAUSED, self.STATE_STOPPED]:
            self.play()

        logger.debug("state toggle: %s", self.state)

        self.last_request_time = time()

    def pause(self, show_matrix=True):
        try:
            self.sonos_controller.pause()
            self.state = self.STATE_PAUSED
            if show_matrix:
                self.nuimo.display_matrix(matrices.PAUSE)
        except SoCoException:
            self.nuimo.display_matrix(matrices.ERROR)

    def play(self, show_matrix=True):
        try:
            self.sonos_controller.play()
            self.state = self.STATE_PLAYING
            if show_matrix:
                self.nuimo.display_matrix(matrices.PLAY)
        except SoCoException:
            self.nuimo.display_matrix(matrices.ERROR)

    def on_swipe_right(self):
        try:
            self.sonos_controller.next()
            if self.state != self.STATE_PLAYING:
                self.play(show_matrix=False)
            self.nuimo.display_matrix(matrices.NEXT_SONG)
        except SoCoException:
            self.nuimo.display_matrix(matrices.ERROR)

        self.last_request_time = time()

    def on_swipe_left(self):
        try:
            self.sonos_controller.previous()
            if self.state != self.STATE_PLAYING:
                self.play(show_matrix=False)
            self.nuimo.display_matrix(matrices.PREVIOUS_SONG)
        except SoCoException:
            self.nuimo.display_matrix(matrices.ERROR)

        self.last_request_time = time()

    def stop(self):
        try:
            self.rendering_control_subscription.unsubscribe()
            self.av_transport_subscription.unsubscribe()
        except Exception:
            # TODO figure out why it's not SoCoException
            logger.exception("Unsubscribe failed")

        self.event_listener.stop()
        super().stop()
