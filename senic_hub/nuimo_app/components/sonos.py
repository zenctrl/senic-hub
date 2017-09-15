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

    def __init__(self, component_config):
        super().__init__(component_config)

        self.sonos_controller = SoCo(component_config['ip_address'])
        self.volume_range = range(0, 100)
        self.event_listener = event_listener  # comes from global scope
        self.state = None
        self.volume = None
        self.nuimo = None
        self.last_request_time = time()

        self.station_id_1 = component_config.get('station1', None)
        self.station_id_2 = component_config.get('station2', None)
        self.station_id_3 = component_config.get('station3', None)

        if not any((self.station_id_1, self.station_id_2, self.station_id_3)):
            try:
                favorites = self.sonos_controller.get_sonos_favorites(max_items=3)
            except SoCoException:
                self.nuimo.display_matrix(matrices.ERROR)
            if favorites['returned'] >= 3:
                self.station_id_1 = favorites['favorites'][0]
                self.station_id_2 = favorites['favorites'][1]
                self.station_id_3 = favorites['favorites'][2]

    def run(self):
        self.subscribe_to_events()
        self.update_state()
        try:
            self.run_loop()
        finally:
            self.unsubscribe_from_events()

    def run_loop(self):
        while not self.stopped:
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
        self.av_transport_subscription = self.sonos_controller.avTransport.subscribe()
        self.rendering_control_subscription = self.sonos_controller.renderingControl.subscribe()

    def unsubscribe_from_events(self):
        self.rendering_control_subscription.unsubscribe()
        self.av_transport_subscription.unsubscribe()

    def update_state(self):
        self.state = self.sonos_controller.get_current_transport_info()['current_transport_state']
        self.volume = self.sonos_controller.volume

        logger.debug("%s state: %s volume: %s", self.sonos_controller.ip_address, self.state, self.volume)

    def on_rotation(self, delta):
        if self.state is not None:
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
        else:
            self.nuimo.display_matrix(matrices.ERROR)
            logger.debug("No Active connection with Host")

    def on_button_press(self):
        if self.state == self.STATE_PLAYING:
            self.pause()
            logger.debug("Play Paused by self.pause() on button press.")

        elif self.state in [self.STATE_PAUSED, self.STATE_STOPPED]:
            self.play()
            logger.debug("Play started/resumed by self.pause() on button press.")

        elif self.state is None:
            self.nuimo.display_matrix(matrices.ERROR)
            logger.debug("No Active connection with Host.")

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

    def on_longtouch_left(self):
        logger.debug("favorite left")
        if self.station_id_1 is not None:
            try:
                self.play_track_playlist_or_album(self.station_id_1, matrices.STATION1)
            except SoCoException:
                self.nuimo.display_matrix(matrices.ERROR)

    def on_longtouch_bottom(self):
        logger.debug("favorite bottom")
        if self.station_id_2 is not None:
            try:
                self.play_track_playlist_or_album(self.station_id_2, matrices.STATION2)
            except SoCoException:
                self.nuimo.display_matrix(matrices.ERROR)

    def on_longtouch_right(self):
        logger.debug("favorite right")
        if self.station_id_3 is not None:
            try:
                self.play_track_playlist_or_album(self.station_id_3, matrices.STATION3)
            except SoCoException:
                self.nuimo.display_matrix(matrices.ERROR)

    def play_track_playlist_or_album(self, src, matrix):
        try:
            if 'object.container.playlistContainer' in src['meta'] or 'object.container.album.musicAlbum' in src['meta']:
                self._replace_queue_with_playlist(src)
                self.sonos_controller.play_from_queue(0)
            else:
                self.sonos_controller.play_uri(uri=src['uri'], meta=src['meta'], title=src['title'])
            self.nuimo.display_matrix(matrix)
        except SoCoException:
            self.nuimo.display_matrix(matrices.ERROR)

    def _replace_queue_with_playlist(self, src):
        """Replace queue with playlist represented by src.

        Playlists can't be played directly with the self.sonos_controller.play_uri
        API as they are actually composed of mulitple URLs. Until soco has
        suppport for playing a playlist, we'll need to parse the playlist item
        and replace the current queue in order to play it.
        """
        import soco
        import xml.etree.ElementTree as ET

        root = ET.fromstring(src['meta'])
        namespaces = {'item':
                      'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/',
                      'desc': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/'}
        desc = root.find('item:item', namespaces).find('desc:desc',
                                                       namespaces).text

        res = [soco.data_structures.DidlResource(uri=src['uri'],
                                                 protocol_info="DUMMY")]
        didl = soco.data_structures.DidlItem(title="DUMMY",
                                             parent_id="DUMMY",
                                             item_id=src['uri'],
                                             desc=desc,
                                             resources=res)

        self.sonos_controller.stop()
        self.sonos_controller.clear_queue()
        self.sonos_controller.play_mode = 'NORMAL'
        self.sonos_controller.add_to_queue(didl)
