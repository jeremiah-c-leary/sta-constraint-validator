from stacv.config import config_location


class PartLocation(config_location.ConfigLocation):

    def set_table(self, sTable):
        self.location = f' in [{sTable}]'

    def set_interface_number(self, iNumber):
        self.location = f' in interface number {iNumber}'

    def set_interface_name(self, sName):
        self.location = f' in interface {sName}'

    def set_pin_number(self, iNumber, sInterfaceName):
        self.location = f' in pin number {iNumber} of interface {sInterfaceName}'

    def set_pin_name(self, sName, sInterfaceName):
        self.location = f' in pin {sName} of interface {sInterfaceName}'

    def set_pin_table(self, sTable, sPinName, sInterfaceName):
        self.location = f' in {sTable} of pin {sPinName} of interface {sInterfaceName}'
