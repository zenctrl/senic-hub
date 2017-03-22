from nuimo import LedMatrix


class LEDMatrixConfig:
    def __init__(self, icon, fading=False, ignore_duplicates=False):
        self.matrix = LedMatrix(icon)
        self.fading = fading
        self.ignore_duplicates = ignore_duplicates
