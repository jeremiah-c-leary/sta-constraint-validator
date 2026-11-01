from stacv.config import config_location


class InterfaceLocation(config_location.ConfigLocation):

    def set_port_number(self, iNumber):
        self.location = f' in port number {iNumber}'

    def set_port_name(self, sName):
        self.location = f' in port {sName}'
