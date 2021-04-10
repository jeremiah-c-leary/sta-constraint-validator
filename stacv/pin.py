

def new(pin_dict):

    if is_clock_pin(pin_dict):
        return build_clock_pin(pin_dict)
    else:
        return build_data_pin(pin_dict)


def is_clock_pin(pin_dict):
    if pin_dict['pin_type'] == 'clock':
        return True
    return False


def build_clock_pin(pin_dict):
    if is_part(pin_dict):
        return build_part_clock_pin(pin_dict)
    else:
        return build_device_clock(pin_dict)


def is_part(pin_dict):
    if pin_dict['location'] == 'part':
        return True
    return False


def build_part_clock_pin(pin_dict):
    if is_input_pin(pin_dict):
        return build_part_input_clock_pin(pin_dict)
    else:
        return build_part_output_clock_pin(pin_dict)


def build_part_input_clock_pin(pin_dict):
    pin = PartInputClockPin(pin_dict['name'])
    pin.max_freq = pin_dict['max_freq']

    return pin


def build_part_output_clock_pin(pin_dict):
    pin = PartOutputClockPin(pin_dict['name'])
    pin.max_freq = pin_dict['max_freq']

    return pin


def build_device_clock(pin_dict):
    if is_output_pin(pin_dict):
        return build_device_output_clock_pin(pin_dict)
    elif is_input_pin(pin_dict):
        return build_device_input_clock_pin(pin_dict)
    else:
        return build_device_internal_clock(pin_dict)


def build_device_output_clock_pin(pin_dict):

    pin = DeviceOutputClockPin(pin_dict['name'])
    pin.frequency = pin_dict['frequency']
    return pin


def build_device_input_clock_pin(pin_dict):

    pin = DeviceInputClockPin(pin_dict['name'])
    pin.frequency = pin_dict['frequency']
    return pin


def build_device_internal_clock(pin_dict):

    pin = DeviceInternalClock(pin_dict['name'])
    pin.frequency = pin_dict['frequency']
    return pin


def build_data_pin(pin_dict):
    if is_device_data_pin(pin_dict):
        return build_device_data_pin(pin_dict)
    else:
        return build_part_data_pin(pin_dict)


def is_device_data_pin(pin_dict):
    if pin_dict['location'] == 'device':
        return True
    return False


def build_device_data_pin(pin_dict):
    if is_output_pin(pin_dict):
        return build_device_output_data_pin(pin_dict)
    else:
        return build_device_input_data_pin(pin_dict)


def is_output_pin(pin_dict):
    if pin_dict['direction'] == 'output':
        return True
    return False


def is_input_pin(pin_dict):
    if pin_dict['direction'] == 'input':
        return True
    return False


def build_device_output_data_pin(pin_dict):
    pin = DeviceOutputDataPin(pin_dict['name'])
    pin.launch_clock = pin_dict['launch_clock']['name']
    pin.launch_edge = pin_dict['launch_clock']['edge']
    pin.capture_clock = pin_dict['capture_clock']['name']
    pin.setup_edge = pin_dict['capture_clock']['edge']['setup']
    pin.hold_edge = pin_dict['capture_clock']['edge']['hold']
    return pin


def build_device_input_data_pin(pin_dict):
    pin = DeviceInputDataPin(pin_dict['name'])
    pin.launch_clock = pin_dict['launch_clock']['name']
    pin.launch_edge = pin_dict['launch_clock']['edge']
    pin.capture_clock = pin_dict['capture_clock']['name']
    pin.setup_edge = pin_dict['capture_clock']['edge']['setup']
    pin.hold_edge = pin_dict['capture_clock']['edge']['hold']
    return pin


def build_part_data_pin(pin_dict):

    if is_part_input_data_pin(pin_dict):
        return build_part_input_data_pin(pin_dict)
    else:
        return build_part_output_data_pin(pin_dict)


def is_part_input_data_pin(pin_dict):
    if pin_dict['direction'] == 'input':
        return True
    return False


def build_part_input_data_pin(pin_dict):
    pin = PartInputDataPin(pin_dict['name'])
    if 'rising' in pin_dict:
        pin.rising_edge_setup = pin_dict['rising']['setup']
        pin.rising_edge_hold = pin_dict['rising']['hold']
    if 'falling' in pin_dict:
        pin.falling_edge_setup = pin_dict['falling']['setup']
        pin.falling_edge_hold = pin_dict['falling']['hold']
    return pin


def build_part_output_data_pin(pin_dict):
    pin = PartOutputDataPin(pin_dict['name'])
    if 'rising' in pin_dict:
        pin.rising_cko_max_id = pin_dict['rising']['max']['id']    
        pin.rising_cko_max = pin_dict['rising']['max']['value']    
        pin.rising_cko_min_id = pin_dict['rising']['min']['id']    
        pin.rising_cko_min = pin_dict['rising']['min']['value']    
    if 'falling' in pin_dict:
        pin.falling_cko_max_id = pin_dict['falling']['max']['id']    
        pin.falling_cko_max = pin_dict['falling']['max']['value']    
        pin.falling_cko_min_id = pin_dict['falling']['min']['id']    
        pin.falling_cko_min = pin_dict['falling']['min']['value']    
    return pin


class Pin():

    def __init__(self, name):
        self.name = name


class PartOutputClockPin(Pin):

    def __init__(self, name):
        Pin.__init__(self, name)
        self.max_freq = None


class PartInputClockPin(Pin):

    def __init__(self, name):
        Pin.__init__(self, name)
        self.max_freq = None


class PartInputDataPin(Pin):

    def __init__(self, name):
        Pin.__init__(self, name)


class PartOutputDataPin(Pin):

    def __init__(self, name):
        Pin.__init__(self, name)
        self.falling_cko_max_id = None
        self.falling_cko_max = None
        self.falling_cko_min_id = None
        self.falling_cko_min = None

        self.rising_cko_max_id = None
        self.rising_cko_max = None
        self.rising_cko_min_id = None
        self.rising_cko_min = None


class DeviceDataPin(Pin):

    def __init__(self, name):
        Pin.__init__(self, name)
        self.launch_clock = None
        self.launch_edge = None
        self.capture_clock = None
        self.setup_edge = None
        self.hold_edge = None


class DeviceOutputDataPin(DeviceDataPin):

    def __init__(self, name):
        DeviceDataPin.__init__(self, name)
        self.direction = 'output'


class DeviceInputDataPin(DeviceDataPin):

    def __init__(self, name):
        DeviceDataPin.__init__(self, name)
        self.direction = 'input'


class DeviceClock(Pin):
    def __init__(self, name):
        Pin.__init__(self, name)
        self.frequency = None


class DeviceOutputClockPin(DeviceClock):

    def __init__(self, name):
        DeviceClock.__init__(self, name)
        self.direction = 'output'


class DeviceInputClockPin(DeviceClock):

    def __init__(self, name):
        DeviceClock.__init__(self, name)
        self.direction = 'input'


class DeviceInternalClock(DeviceClock):

    def __init__(self, name):
        DeviceClock.__init__(self, name)
        self.direction = 'internal'
