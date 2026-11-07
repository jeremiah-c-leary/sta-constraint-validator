
class Pin():

    def __init__(self):
        self.name = None
        self.methodology = None
        self.if_signal = None
        self.clock = None
        self.capture_edge = None
        self.launch_edge = None
        self.setup = None
        self.hold = None
        self.cko_max = None
        self.cko_min = None
        # An output can give its timing as the window its data is valid in, instead of a clock to out.
        self.valid_before = None
        self.valid_after = None
