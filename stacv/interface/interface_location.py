from stacv.config import config_location


class InterfaceLocation(config_location.ConfigLocation):

    def set_port_number(self, iNumber):
        self.location = f' in port number {iNumber}'

    def set_port_name(self, sName):
        self.location = f' in port {sName}'

    def set_clock_number(self, iNumber):
        self.location = f' of clock number {iNumber}'

    def set_clock_name(self, sName):
        self.location = f' of clock {sName}'

    def set_generator(self, sClockName):
        self.location = f' in generator of clock {sClockName}'

    def set_port_table(self, sTable, sPortName):
        self.location = f' in {sTable} of port {sPortName}'
