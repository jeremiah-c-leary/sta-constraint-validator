
class Interface():
    def __init__(self):
        self.description = None
        self.interface_name = None
        self.ports = []


class Port():
    def __init__(self):
        self.name = None
        self.methodology = None
        self.timing_reports = []


class ConfigLocation():

    def __init__(self, sFilename):
        self.filename = sFilename
        self.location = ''

    def set_port_number(self, iNumber):
        self.location = f' in port number {iNumber}'  

    def set_port_name(self, sName):
        self.location = f' in port {sName}'  
