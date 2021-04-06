
from . import pin


def new(interface_dict):
    name = list(interface_dict.keys())[0]
    if is_part_interface(name, interface_dict):
        return build_part_interface(name, interface_dict)
    else:
        return build_device_interface(name, interface_dict)


def is_part_interface(name, interface_dict):
    if 'timing_model' in interface_dict[name]:
        return True
    return False


def build_part_interface(name, interface_dict):
    interface = PartInterface(name)
    interface.timing_model = interface_dict[name]['timing_model']
    interface.clock_pin = pin.new(interface_dict[name]['clock'])
    interface.data_pins = build_data_pin_list(interface_dict[name]['data'])

    return interface


def build_device_interface(name, interface_dict):
    interface = DeviceInterface(name)
    interface.external_clock = pin.new(interface_dict[name]['external_clock'])
    interface.internal_clock = pin.new(interface_dict[name]['internal_clock'])
    interface.data_pins = build_data_pin_list(interface_dict[name]['data'])
    return interface


def build_data_pin_list(data_pin_list):
    data_pins = []

    for data_pin in data_pin_list:
        new_data_pin = pin.new(data_pin)
        data_pins.append(new_data_pin)

    return data_pins


class Interface():

    def __init__(self, name):
        self.name = name


class PartInterface(Interface):

    def __init__(self, name):
        Interface.__init__(self, name)
        self.timing_model = None

    def has_pin_named(self, pin_name):
        if self.clock_pin.name == pin_name:
            return True
        for data_pin in self.data_pins:
            if data_pin.name == pin_name:
                return True
        return False


class DeviceInterface(Interface):

    def __init__(self, name):
        Interface.__init__(self, name)
        self.internal_clock = None
        self.external_clock = None
        self.data_pins = None

    def get_pin_named(self, pin_name):
        for data_pin in self.data_pins:
            if data_pin.name == pin_name:
                return data_pin
        if self.internal_clock.name == pin_name:
            return self.internal_clock
        if self.external_clock.name == pin_name:
            return self.external_clock

    def get_clock_named(self, clock_name):
        if self.internal_clock.name == clock_name:
            return self.internal_clock
