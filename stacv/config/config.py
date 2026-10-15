
class InterfaceConfig():
    def __init__(self):
        self.description = None
        self.interfaces = []


class Interface():
    def __init__(self):
        self.name = None
        self.ports = []


class Port():
    def __init__(self):
        self.name = None
        self.methodology = None
        self.timing_reports = []


class ConfigLocation():

    def __init__(self, sFilename):
        self.filename = sFilename
        self.interface_location = ''
        self.interface_number = None
        self.interface_names = {}
        self.location = self.interface_location

    def get_number_of_interface_named(self, sName):
        return self.interface_names[sName]

    def set_interface_number(self, iNumber):
        self.interface_location = f' in interface number {iNumber}'
        self.location = self.interface_location
        self.interface_number = iNumber

    def set_interface_name(self, sName):
        self.interface_location = f' in interface {sName}'
        self.location = self.interface_location
        self.interface_names[sName] = self.interface_number

    def set_port_number(self, iNumber):
        self.location = self.interface_location + f' port number {iNumber}'  

    def set_port_name(self, sName):
        self.location = self.interface_location + f' port {sName}'  
