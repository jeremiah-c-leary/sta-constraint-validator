
from . import interface


def new(part_dict):

    part = Part(part_dict['vendor'], part_dict['name'])

    part.interfaces = build_interface_list(part_dict)

    return part


def build_interface_list(part_dict):

    interfaces = []
    for interface_dict in part_dict['interface']:
        name = list(interface_dict.keys())[0]
        my_interface = interface_dict[name]
        my_interface['name'] = name
        my_interface['location'] = 'part'
        new_interface = interface.new(my_interface)

        interfaces.append(new_interface)

    return interfaces


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
