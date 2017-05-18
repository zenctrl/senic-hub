import logging
from pprint import pformat
from threading import Thread
from .. import matrices
from ..hass import HomeAssistant


logger = logging.getLogger(__name__)


def clamp_value(value, range_):
    return min(max(value, range_.start), range_.stop)


class BaseComponent:
    MATRIX = matrices.ERROR

    def __init__(self, component_id, config):
        self.component_id = component_id

    def start(self):
        pass

    def stop(self):
        pass


class ThreadComponent(BaseComponent):
    def __init__(self, component_id, config):
        super().__init__(component_id, config)
        self.stopping = True
        self.thread = None

    def run(self):
        """
        Concrete components must implement run() method
        """
        raise NotImplementedError()

    def start(self):
        self.stopping = False
        self.thread = Thread(target=self.run)
        self.thread.start()

    def stop(self):
        self.stopping = True


class HomeAssistantComponent(BaseComponent):
    def __init__(self, ha_domain, component_id, config):
        super().__init__(component_id, config)

        self.is_on = False

        # TODO: Parametrize HA's address?
        self._ha_address = "localhost:8123"
        self._ha_entity_id = config['entity_id']
        self._ha_domain = ha_domain

    def start(self):
        super().start()

        # TODO: Provide single HA instance to all HA-based components
        self._ha = HomeAssistant(self._ha_address, on_connect=self._ha_connected, on_disconnect=self._ha_disconnected)
        self._ha.start()
        self._ha.register_state_listener(self._ha_entity_id, self._ha_state_changed)

    def stop(self):
        super().stop()
        self._ha.stop()
        self._ha.unregister_state_listener(self._ha_entity_id)

    def run(self):
        pass

    def update_from_ha_state(self, state):
        self.is_on = state.get('state', None) != 'off'

    def call_ha_service(self, service, data={}, on_success=None, on_error=None):
        def _on_success(result):
            logger.debug("Calling service %s:%s succeeded with result: %s", self._ha_domain, service, pformat(result))

        def _on_error():
            logger.debug("Failed calling service %s:%s", self._ha_domain, service)

        data["entity_id"] = self._ha_entity_id
        logger.debug("Call service %s:%s with data: %s", self._ha_domain, service, pformat(data))
        self._ha.call_service(self._ha_domain, service, data, on_success or _on_success, on_error or _on_error)

    def _ha_connected(self):
        def on_state_retrieved(state):
            self._ha_state_changed(state)

        def on_state_retrieve_failed():
            logger.debug("HA get state failed")

        self._ha.get_state(self._ha_entity_id, on_state_retrieved, on_state_retrieve_failed)

    def _ha_disconnected(self):
        pass

    def _ha_state_changed(self, state):
        if "data" in state:
            self.update_from_ha_state(state["data"]["new_state"])
        else:
            self.update_from_ha_state(state)
