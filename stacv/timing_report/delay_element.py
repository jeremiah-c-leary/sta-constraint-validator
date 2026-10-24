
class Delay():
    def __init__(self):
        self.delay = None
        self.resource = None
        self.line = None


class CellDelay(Delay):
    def __init__(self):
        Delay.__init__(self)
        self.location = None
        self.delay_type = None


class NetDelay(Delay):
    def __init__(self):
        Delay.__init__(self)
        self.fan_out = None
