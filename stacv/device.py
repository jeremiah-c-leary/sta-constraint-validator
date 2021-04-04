
#from . import interface


def new(device_dict):

    device = Device(device_dict['vendor'], device_dict['name'])

#    interfaces = []
#    for interface_dict in device_dict['interface'].items():
#        new_interface = interface.new(interface_dict[0], interface_dict[1])
#
#        interfaces.append(new_interface)
#
#    device.interfaces = interfaces

    return device


class Device():

    def __init__(self, vendor, name):
        self.vendor = vendor
        self.name = name
#        self.interfaces = []
#
#    def get_interface_with_pin_named(self, pin_name):
#        for my_interface in self.interfaces:
#            if my_interface.has_pin_named(pin_name):
#                return my_interface
#        return None
