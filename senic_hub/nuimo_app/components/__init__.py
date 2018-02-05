import logging

from threading import Thread
from .. import matrices


logger = logging.getLogger(__name__)


def clamp_value(value, range_):
    return min(max(value, range_.start), range_.stop)


class BaseComponent:
    MATRIX = matrices.ERROR

    def __init__(self, component_config):
        self.component_id = component_config['id']
        self.ip_address = component_config.get('ip_address', None)
        self.stopped = True

    def start(self):
        self.stopped = False

    def stop(self):
        self.stopped = True

    def on_longtouch_left(self):
        pass

    def on_longtouch_bottom(self):
        pass

    def on_longtouch_right(self):
        pass


class ThreadComponent(BaseComponent):
    def __init__(self, component_config):
        super().__init__(component_config)
        self.thread = None
        self.component_name = component_config['name']

    def start(self):
        super().start()
        self.thread = Thread(target=self._run,
                             name=self.component_name,
                             daemon=True)
        self.thread.start()

    def _run(self):
        try:
            self.run()
        except Exception as e:
            logger.error("Failure while running component '%s'")
            logger.exception(e)
        finally:
            self.stopped = True

    def run(self):
        """
        Concrete components must implement run() method
        """
        raise NotImplementedError()
