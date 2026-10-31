class Interface():
    def __init__(self):
        self.description = None
        self.interface_name = None
        self.clocks = []
        self.ports = []

    def get_clock_named(self, sClockName):
        for oClock in self.clocks:
            if oClock.name == sClockName:
                return oClock
        return None
