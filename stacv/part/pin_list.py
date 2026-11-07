class PinList():

    def __init__(self):
        self.pins = []

    def get_pin_named(self, sPinName, sMethodology=None):
        # A bidirectional pin has a table for each methodology, so the methodology picks one.
        # A clock pin carries no timing, so it is not one of the pins looked up by name.
        for oPin in self.pins:
            if oPin.methodology is None:
                continue
            if oPin.name == sPinName and (sMethodology is None or oPin.methodology == sMethodology):
                return oPin
        return None

    def get_pins_with_signal(self, sSignal):
        lPins = []
        for oPin in self.pins:
            if oPin.if_signal == sSignal:
                lPins.append(oPin)
        return lPins

    def has_pin_named(self, sPinName):
        return self.get_pin_named(sPinName) is not None
