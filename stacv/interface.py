
from . import pin


def new(interface_dict):
    name = list(interface_dict.keys())[0]
    interface = Interface(name)
    interface.timing_model = interface_dict[name]['timing_model']
    interface.clock_pin = pin.new(interface_dict[name]['clock'])

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
        self.timing_model = None

    def has_pin_named(self, pin_name):
        if self.clock_pin.name == pin_name:
            return True
        for data_pin in self.data_pins:
            if data_pin.name == pin_name:
                return True
        return False
