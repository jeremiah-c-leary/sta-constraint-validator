
class Clock():

    def __init__(self):
        self.name = None
        self.period = None
        self.port = None
        self.generator = None
        # None for a clock that runs all the time; "low" or "high" for a clock that stops.
        self.idle = None
        # The time, in ns, the clock's edges are shifted by, such as a PLL's phase shift.
        self.phase = 0.0
