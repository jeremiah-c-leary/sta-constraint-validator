
from . import interface


def new(part_dict):

    part = Part(part_dict['vendor'], part_dict['name'])
    
    interfaces = []
    for interface_dict in part_dict['interface']:
        new_interface = interface.new(interface_dict)

        interfaces.append(new_interface)

    part.interfaces = interfaces

    return part


class Part():

    def __init__(self, vendor, name):
        self.vendor = vendor
        self.name = name
        self.interfaces = []

    def get_interface_with_pin_named(self, pin_name):
        for my_interface in self.interfaces:
            if my_interface.has_pin_named(pin_name):
                return my_interface
        return None
