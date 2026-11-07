
class Interface():

    def __init__(self):
        self.name = None
        # The interface standard the part interface follows, and the part's role in it.
        self.if_standard = None
        self.if_role = None
        self.clock_pins = []
        self.pins = None

    def has_pin_named(self, sPinName):
        return self.pins.has_pin_named(sPinName)

    def get_pin_named(self, sPinName, sMethodology=None):
        return self.pins.get_pin_named(sPinName, sMethodology)
