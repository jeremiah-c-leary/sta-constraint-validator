
class ClockPin():

    def __init__(self):
        self.port = None
        self.name = None
        self.period = None
        self.generator = None
        self.idle = None
        self.phase = 0.0
        self.setup_edge = None
        self.hold_edge = None
