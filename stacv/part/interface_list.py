class InterfaceList():

    def __init__(self):
        self.interfaces = []

    def get_pin_named(self, sPinName, sMethodology=None, sInterfaceName=None):
        for oInterface in self.interfaces:
            if sInterfaceName is not None and oInterface.name != sInterfaceName:
                continue
            oPin = oInterface.get_pin_named(sPinName, sMethodology)
            if oPin is not None:
                return oPin
        return None

    def has_pin_named(self, sPinName):
        return self.get_pin_named(sPinName) is not None

    def get_interface_named(self, sInterfaceName):
        for oInterface in self.interfaces:
            if oInterface.name == sInterfaceName:
                return oInterface
        return None
