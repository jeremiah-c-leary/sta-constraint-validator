class PinList():

    def __init__(self):
        self.pins = []

    def get_pin_named(self, sPinName, sMethodology=None):
        # A bidirectional pin has a table for each methodology, so the methodology picks one.
        for oPin in self.pins:
            if oPin.name == sPinName and (sMethodology is None or oPin.methodology == sMethodology):
                return oPin
        return None

    def has_pin_named(self, sPinName):
        return self.get_pin_named(sPinName) is not None
