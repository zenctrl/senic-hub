import logging
from pprint import pformat
from time import time
from . import HomeAssistantComponent
from .. import matrices


logger = logging.getLogger(__name__)


class Component(HomeAssistantComponent):
    MATRIX = matrices.MUSIC_NOTE

    VOLUME_CHANGE_RESPONSE_TIMEOUT = 5.0

    def __init__(self, component_id, config):
        super().__init__("media_player", component_config)

        self.playback_state = None
        self.volume = None
        self.is_volume_request_pending = False
        self.last_volume_request_time = 0
        self.should_send_volume_again = False

    def update_from_ha_state(self, state):
        super().update_from_ha_state(state)
        logger.debug("Updated media player state: %s", pformat(state))
        self.playback_state = state.get('state', None)
        if self.is_on:
            received_volume = state.get('attributes', {}).get('volume_level', None)
        else:
            received_volume = None
        if received_volume is not None:
            # Only overwrite our volume if we haven't recently modified it ourselves
            # This avoids synching with an old volume while the user is still turning the wheel
            if time() - self.last_volume_request_time > Component.VOLUME_CHANGE_RESPONSE_TIMEOUT:
                self.volume = received_volume
        else:
            self.volume = None
        logger.debug("Is On: %s, Volume: %s, Playback State: %s", self.is_on, self.volume, self.playback_state)

    def on_rotation(self, delta):
        # TODO: `delta` can be passed in as already normalized, i.e. div. by 1800
        if self.volume is None:
            self.nuimo.display_matrix(matrices.ERROR)
            return
        self.volume = min(max(self.volume + delta, 0.0), 1.0)
        self.send_volume()
        self.nuimo.display_matrix(matrices.progress_bar(self.volume), fading=True, ignore_duplicates=True)

    def on_button_press(self):
        # TODO: When triggering play state change, we won't know very soon which new state the player is in.
        #       This said, when the user continuosly presses the button we can't quickly switch playback state yet.
        if not self.is_on:
            self.call_ha_service("turn_on")

        if self.playback_state == 'playing':
            self.nuimo.display_matrix(matrices.PAUSE)
            self.call_ha_service("media_pause")
        else:
            self.nuimo.display_matrix(matrices.PLAY)
            self.call_ha_service("media_play")

    def on_swipe_right(self):
        logger.debug("swipe right")

    def on_swipe_left(self):
        logger.debug("swipe left")

    def send_volume(self):
        if (self.is_volume_request_pending and
                (time() - self.last_volume_request_time < Component.VOLUME_CHANGE_RESPONSE_TIMEOUT)):
            logger.debug("Delay volume sending, previous volume service call still in progress")
            self.should_send_volume_again = True
            return

        logger.debug("Make volume service call with volume %s", self.volume)

        def on_success(result):
            logger.debug("Volume service call succeeded")
            self.is_volume_request_pending = False
            if self.should_send_volume_again:
                self.should_send_volume_again = False
                logger.debug("Make another volume service call since Nuimo's wheel has been rotated in the meanwhile")
                self.send_volume()

        def on_error():
            logger.debug("Volume service call failed")
            self.is_volume_request_pending = False

        self.is_volume_request_pending = True
        self.last_volume_request_time = time()
        self.call_ha_service("volume_set", {"volume_level": self.volume}, on_success, on_error)
