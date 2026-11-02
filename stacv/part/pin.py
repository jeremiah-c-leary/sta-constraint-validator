
class Pin():

    def __init__(self):
        self.name = None
        self.methodology = None
        self.clock = None
        self.capture_edge = None
        self.launch_edge = None
        self.setup = None
        self.hold = None
        self.cko_max = None
        self.cko_min = None
        # The second form of each kind of pin: a skew window for an input, a valid window for an output.
        self.skew_min = None
        self.skew_max = None
        self.valid_before = None
        self.valid_after = None
