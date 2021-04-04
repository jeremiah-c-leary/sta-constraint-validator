
from . import interface


def new(part_dict):

    part = Part(part_dict['vendor'], part_dict['name'])

    interfaces = []
    for interface_dict in part_dict['interface'].items():
        new_interface = interface.new(interface_dict[0], interface_dict[1])

        interfaces.append(new_interface)

    part.interfaces = interfaces

    return part


class Part():

    def __init__(self, vendor, name):
        self.vendor = vendor
        self.name = name
        self.interfaces = []
