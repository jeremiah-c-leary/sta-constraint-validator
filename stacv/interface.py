
from . import pin


def new(name, interface_dict):

    interface = Interface(name)
    interface.timing_model = interface_dict['timing_model']
    interface.clock_pin = pin.new(interface_dict['clock'])

    data_pins = []

    for data_pin in interface_dict['data'].items():
        new_data_pin = pin.new(extract_data_dict(data_pin))
        data_pins.append(new_data_pin)

    interface.data_pins = data_pins

    return interface


class Interface():

    def __init__(self, name):
        self.name = name
        self.timing_model = None


def extract_data_dict(dict_key_value_pair):
    temp = {}
    temp[dict_key_value_pair[0]] = dict_key_value_pair[1]
    return temp
