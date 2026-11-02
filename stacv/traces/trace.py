
class Trace():

    def __init__(self):
        self.name = None
        self.device_pin = None
        self.part_pin = None
        self.device_to_part = None
        self.part_to_device = None
        # A trace from a clock source names the source, and runs to the device or to the part.
        self.source = None
        self.source_to_device = None
        self.source_to_part = None
