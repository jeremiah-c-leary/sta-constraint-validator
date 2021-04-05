
from . import interface


def new(device_dict):

    device = Device(device_dict['vendor'], device_dict['name'])

    device.interfaces = build_interface_list(device_dict)

    return device


def build_interface_list(device_dict):
    interfaces = []

    for interface_dict in device_dict['interface']:

        new_interface = interface.new(interface_dict)

        interfaces.append(new_interface)

    return interfaces


class Device():

    def __init__(self, vendor, name):
        self.vendor = vendor
        self.name = name
        self.interfaces = []

    def get_interface_named(self, name):
        for my_interface in self.interfaces:
            if my_interface.name == name:
                return my_interface
        return None