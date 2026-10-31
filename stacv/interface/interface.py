from stacv.interface import port


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

    def get_analyzed_ports(self):
        lPorts = []
        for oPort in self.ports:
            if oPort.status == port.ANALYZE:
                lPorts.append(oPort)
        return lPorts
