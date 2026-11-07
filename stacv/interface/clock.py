
class Clock():

    def __init__(self):
        self.name = None
        self.period = None
        self.port = None
        self.generator = None
        # None for a clock that runs all the time; "low" or "high" for a clock that stops.
        self.idle = None
        # The signal of the interface standard the clock's port carries, such as SCK.
        self.if_signal = None
