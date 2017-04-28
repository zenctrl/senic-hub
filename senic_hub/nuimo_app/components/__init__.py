from threading import Thread

from .. import matrices


NUIMO_ENCODER_RING_POINTS = 1800


def clamp_value(value, range_):
    return min(max(value, range_.start), range_.stop)


def normalize_delta(points, max_value):
    return points / NUIMO_ENCODER_RING_POINTS * max_value


class BaseComponent:
    MATRIX = matrices.ERROR

    def __init__(self, config):
        self.name = config['name']

    def run(self):
        """
        Concrete components must implement run() method
        """
        raise NotImplementedError()

    def start(self):
        self.thread = Thread(target=self.run)
        self.thread.start()

    def stop(self):
        self.stopping = True
