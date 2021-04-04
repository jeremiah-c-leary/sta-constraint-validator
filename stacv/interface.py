
from . import pin


def new(name, interface_dict):

    interface = Interface(name)
    interface.timing_model = interface_dict['timing_model']
    interface.clock_pin = pin.new(interface_dict['clock'])

    data_pins = []

    for data_pin_name in interface_dict['data']:
        dTemp = {}
        dTemp[data_pin_name] = interface_dict['data'][data_pin_name]
        data_pin = pin.new(dTemp)
        data_pins.append(data_pin)

    interface.data_pins = data_pins

    return interface


class Interface():

    def __init__(self, name):
        self.name = name
        self.timing_model = None
