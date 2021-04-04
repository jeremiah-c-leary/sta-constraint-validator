
#from . import interface


def new(pin_dict):

    pin_name = list(pin_dict.keys())[0]
    if 'max_freq' in pin_dict[pin_name]:
        pin = ClockPin(pin_name)
        pin.max_freq = pin_dict[pin_name]['max_freq']
    else:
        clock_edge = list(pin_dict[pin_name].keys())[0]

        if 'setup' in pin_dict[pin_name][clock_edge]:
            pin = InputPin(pin_name)
            pin.edge = clock_edge
            pin.setup = pin_dict[pin_name][clock_edge]['setup']
            pin.hold = pin_dict[pin_name][clock_edge]['hold']
        else:
            pin = OutputPin(pin_name)
            pin.edge = clock_edge
            pin.cko_max = pin_dict[pin_name][clock_edge]['clock_to_out']['max']
            pin.cko_min = pin_dict[pin_name][clock_edge]['clock_to_out']['min']

    return pin


class Pin():

    def __init__(self, name):
        self.name = name


class ClockPin(Pin):

    def __init__(self, name):
        Pin.__init__(self, name)
        self.max_freq = None


class InputPin(Pin):

    def __init__(self, name):
        Pin.__init__(self, name)
        self.setup = None
        self.hold = None
        self.edge = None


class OutputPin(Pin):

    def __init__(self, name):
        Pin.__init__(self, name)
        self.cko_max = None
        self.cko_min = None
        self.edge = None
