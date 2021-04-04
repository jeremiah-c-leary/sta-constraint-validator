
from . import interface


def new(part_dict):

    part = Part(part_dict['vendor'], part_dict['name'])

    lInterfaces = []
    for interface_name in part_dict['interface']:
        new_interface = interface.new(interface_name, part_dict['interface'][interface_name])

        lInterfaces.append(new_interface)

    part.interfaces = lInterfaces

    return part


class Part():

    def __init__(self, vendor, name):
        self.vendor = vendor
        self.name = name
        self.interfaces = []
