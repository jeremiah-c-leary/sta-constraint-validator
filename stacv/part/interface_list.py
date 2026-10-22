
class InterfaceList():

    def __init__(self):
        self.interfaces = []

    def add_interface(self, oInterface):
        self.interfaces.append(oInterface)

    def get_pin_named(self, sPinName):
        for oInterface in self.interfaces:
            if oInterface.has_pin_named(sPinName):
                return oInterface.get_pin_named(sPinName)
        return None
