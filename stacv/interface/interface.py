from stacv.interface import port


class Interface():
    def __init__(self):
        self.description = None
        self.interface_name = None
        # The part and traces paths as written, and resolved once a command needs the files.
        self.part_as_written = None
        self.traces_as_written = None
        self.part = None
        # The interface of the part this file times, or None for every interface of the part.
        self.part_interface = None
        self.traces = None
        # The interface standard the file follows, such as "SPI mode 1", and the device's role in it; None when it follows none.
        self.if_standard = None
        self.if_role = None
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
