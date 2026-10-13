
class Config():
    def __init__(self):
        self.description = None
        self.interfaces = []

    def add_interface(self, oInterface):
        self.interfaces.append(oInterface)


class Interface():
    def __init__(self):
        self.name = None
        self.ports = []

    def add_port(self, oPort):
        self.ports.append(oPort)


class Port():
    def __init__(self):
        self.name = None
        self.methodology = None
        self.timing_reports = []

    def add_timing_report(self, sTimingReport):
        self.timing_reports.append(sTimingReport)
