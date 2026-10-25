class ConfigLocation():

    def __init__(self, sFilename):
        self.filename = sFilename
        self.location = ''

    def set_port_number(self, iNumber):
        self.location = f' in port number {iNumber}'

    def set_port_name(self, sName):
        self.location = f' in port {sName}'
