
from . import interface


def new(device_dict):

    device = Device(device_dict['vendor'], device_dict['name'])

    device.interfaces = build_interface_list(device_dict)

    return device


def build_interface_list(device_dict):
    interfaces = []
    for interface_dict in device_dict['interface']:
        name = list(interface_dict.keys())[0]
        my_interface = interface_dict[name]
        my_interface['name'] = name
        my_interface['location'] = 'device'
        new_interface = interface.new(my_interface)

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

    def get_interface_names(self):
        names = []
        for my_interface in self.interfaces:
            names.append(my_interface.name)
        return names

    def get_data_pins_from_interface_named(self, name):
        my_interface = self.get_interface_named(name)
        return my_interface.data_pins
