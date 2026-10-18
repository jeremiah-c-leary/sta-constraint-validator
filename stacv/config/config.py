
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
        self.location = self.interface_location

    def set_port_number(self, iNumber):
        self.location = self.interface_location + f' in port number {iNumber}'  

    def set_port_name(self, sName):
        self.location = self.interface_location + f' in port {sName}'  
