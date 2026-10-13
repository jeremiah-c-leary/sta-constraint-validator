
class InterfaceConfig():
    def __init__(self):
        self.description = None
        self.interfaces = []


class Interface():
    def __init__(self):
        self.name = None
        self.ports = []


class Port():
    def __init__(self):
        self.name = None
        self.methodology = None
        self.timing_reports = []
