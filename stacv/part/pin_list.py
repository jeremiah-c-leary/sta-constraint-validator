
class PinList():

    def __init__(self):
        self.pins = []

    def get_pin_named(self, sPinName):
        for oPin in self.pins:
            if oPin.name == sPinName:
                return oPin
        return None

    def has_pin_named(self, sPinName):
        for oPin in self.pins:
            if oPin.name == sPinName:
                return True
        return False
