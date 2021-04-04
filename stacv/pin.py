

def new(pin_dict):

    pin_name = list(pin_dict.keys())[0]
    if is_part_clock_pin(pin_dict[pin_name]):
        return build_part_clock_pin(pin_name, pin_dict)
    elif is_device_clock_pin(pin_dict[pin_name]):
        return build_device_clock_pin(pin_name, pin_dict)
    else:
        return build_data_pin(pin_name, pin_dict)


def is_part_clock_pin(pin_dict):
    if 'max_freq' in pin_dict:
        return True
    return False


def is_device_clock_pin(pin_dict):
    if 'frequency' in pin_dict:
        return True
    return False


def build_part_clock_pin(pin_name, pin_dict):
    pin = ClockPin(pin_name)
    pin.max_freq = pin_dict[pin_name]['max_freq']

    return pin


def build_device_clock_pin(pin_name, pin_dict):
    pin = ClockPin(pin_name)
    pin.max_freq = pin_dict[pin_name]['frequency']
    return pin


def build_data_pin(pin_name, pin_dict):
    if is_device_data_pin(pin_dict[pin_name]):
        return build_device_data_pin(pin_name, pin_dict)
    else:
        return build_part_data_pin(pin_name, pin_dict)


def is_device_data_pin(pin_dict):
    if 'clock_edges' in pin_dict:
        return True
    return False


def build_device_data_pin(pin_name, pin_dict):
    if is_device_output_data_pin(pin_dict[pin_name]):
        return build_device_output_data_pin(pin_name, pin_dict)
    else:
        return build_device_input_data_pin(pin_name, pin_dict)   


def is_device_output_data_pin(pin_dict):
    if 'launch_clock' in pin_dict:
        return True
    return False


def build_device_output_data_pin(pin_name, pin_dict):
    pin = DeviceOutputPin(pin_name)
    pin.launch_clock = pin_dict[pin_name]['launch_clock']
    pin.launch_edge = pin_dict[pin_name]['clock_edges']['from']
    pin.setup_edge = pin_dict[pin_name]['clock_edges']['setup']
    pin.hold_edge = pin_dict[pin_name]['clock_edges']['hold']
    return pin


def build_device_input_data_pin(pin_name, pin_dict):
    pin = DeviceInputPin(pin_name)
    pin.capture_clock = pin_dict[pin_name]['capture_clock']
    pin.capture_edge = pin_dict[pin_name]['clock_edges']['from']
    pin.setup_edge = pin_dict[pin_name]['clock_edges']['setup']
    pin.hold_edge = pin_dict[pin_name]['clock_edges']['hold']
    return pin


def build_part_data_pin(pin_name, pin_dict):
    clock_edge = list(pin_dict[pin_name].keys())[0]
    
    if is_part_input_data_pin(pin_dict[pin_name][clock_edge]):
        return build_part_input_data_pin(pin_name, pin_dict)
    else:
        return build_part_output_data_pin(pin_name, pin_dict)


def is_part_input_data_pin(pin_dict):
    if 'setup' in pin_dict:
        return True
    return False


def build_part_input_data_pin(pin_name, pin_dict):
    clock_edge = list(pin_dict[pin_name].keys())[0]
    pin = InputPin(pin_name)
    pin.edge = clock_edge
    pin.setup = pin_dict[pin_name][clock_edge]['setup']
    pin.hold = pin_dict[pin_name][clock_edge]['hold']
    return pin


def build_part_output_data_pin(pin_name, pin_dict):
    clock_edge = list(pin_dict[pin_name].keys())[0]
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


class DeviceOutputPin(Pin):

    def __init__(self, name):
        Pin.__init__(self, name)
        self.launch_clock = None
        self.launch_edge = None
        self.setup_edge = None
        self.hold_edge = None


class DeviceInputPin(Pin):

    def __init__(self, name):
        Pin.__init__(self, name)
        self.capture_clock = None
        self.capture_edge = None
        self.setup_edge = None
        self.hold_edge = None
