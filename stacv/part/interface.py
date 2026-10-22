
class Interface():

    def __init__(self):
        self.name = None
        self.pins = None

    def has_pin_named(self, sPinName):
        return self.pins.has_pin_named(sPinName)

    def get_pin_named(self, sPinName):
        return self.pins.get_pin_named(sPinName)
