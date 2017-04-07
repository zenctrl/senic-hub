from threading import Thread

from .. import matrices


class EncoderRing:
    NUM_POINTS = 1800

    def __init__(self, min_value, max_value):
        self.min_value = min_value
        self.max_value = max_value

    def points_to_value(self, points):
        return points / self.NUM_POINTS * self.max_value

    def clamp_value(self, value):
        return min(max(value, self.min_value), self.max_value)


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
