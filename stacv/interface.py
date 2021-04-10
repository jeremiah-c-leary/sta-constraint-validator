
from . import pin


def new(interface_dict):
    if is_part_interface(interface_dict):
        return build_part_interface(interface_dict)
    else:
        return build_device_interface(interface_dict)


def is_part_interface(interface_dict):
    if interface_dict['location'] == 'part':
        return True
    return False


def build_part_interface(interface_dict):
    interface = PartInterface(interface_dict['name'])
    interface.timing_model = interface_dict['timing_model']
    interface.clocks = build_part_clock_pin_list(interface_dict)
    interface.data_pins = build_part_data_pin_list(interface_dict)

    return interface


def build_part_clock_pin_list(interface_dict):
    clock_pins = []
    if has_input_clocks(interface_dict):
        clock_pins.extend(build_part_input_clock_pin_list(interface_dict))
    if has_output_clocks(interface_dict):
        clock_pins.extend(build_part_output_clock_pin_list(interface_dict))
    return clock_pins


def has_input_clocks(interface_dict):
    if 'input' in interface_dict['clock']:
        return True
    return False


def has_output_clocks(interface_dict):
    if 'output' in interface_dict['clock']:
        return True
    return False


def build_part_input_clock_pin_list(interface_dict):
    clock_pins = []
    for my_pin in interface_dict['clock']['input']:
        clock_dict = {}
        clock_dict['location'] = 'part'
        clock_dict['direction'] = 'input'
        clock_dict['pin_type'] = 'clock'
        name = list(my_pin.keys())[0]
        clock_dict['name'] = name
        clock_dict['max_freq'] = my_pin[name]['max_freq']
        clock_pins.append(pin.new(clock_dict))

    return clock_pins


def build_part_output_clock_pin_list(interface_dict):
    clock_pins = []
    for my_pin in interface_dict['clock']['output']:
        clock_dict = {}
        clock_dict['location'] = 'part'
        clock_dict['direction'] = 'output'
        clock_dict['pin_type'] = 'clock'
        name = list(my_pin.keys())[0]
        clock_dict['name'] = name
        clock_dict['max_freq'] = my_pin[name]['max_freq']
        clock_pins.append(pin.new(clock_dict))

    return clock_pins


def build_part_data_pin_list(interface_dict):
    data_pins = []
    if has_input_data_pins(interface_dict):
        data_pins.extend(build_part_input_data_pin_list(interface_dict))
    if has_output_data_pins(interface_dict):
        data_pins.extend(build_part_output_data_pin_list(interface_dict))
    return data_pins


def has_input_data_pins(interface_dict):
    if 'input' in interface_dict['data']:
        return True
    return False


def has_output_data_pins(interface_dict):
    if 'output' in interface_dict['data']:
        return True
    return False


def build_part_input_data_pin_list(interface_dict):
    data_pins = []
    for my_pin in interface_dict['data']['input']:
        pin_dict = {}
        pin_dict['location'] = 'part'
        pin_dict['direction'] = 'input'
        pin_dict['pin_type'] = 'data'
        name = list(my_pin.keys())[0]
        pin_dict['name'] = name
        pin_dict['clock'] = my_pin[name]['clock']
        if has_rising_edge(my_pin[name]):
            pin_dict['rising'] = build_part_input_edge(my_pin[name]['rising'])
        if has_falling_edge(my_pin[name]):
            pin_dict['falling'] = build_part_input_edge(my_pin[name]['falling'])
        data_pins.append(pin.new(pin_dict))
    return data_pins


def has_rising_edge(pin_dict):
    if 'rising' in pin_dict:
        return True
    return False


def has_falling_edge(pin_dict):
    if 'falling' in pin_dict:
        return True
    return False


def build_part_input_edge(edge_dict):
    edge = {}
    edge['setup'] = edge_dict['setup']
    edge['hold'] = edge_dict['hold']
    return edge


def build_part_output_data_pin_list(interface_dict):
    data_pins = []
    for my_pin in interface_dict['data']['output']:
        pin_dict = {}
        pin_dict['location'] = 'part'
        pin_dict['direction'] = 'output'
        pin_dict['pin_type'] = 'data'
        name = list(my_pin.keys())[0]
        pin_dict['name'] = name
        pin_dict['clock'] = my_pin[name]['clock']
        if has_rising_edge(my_pin[name]):
            pin_dict['rising'] = build_part_output_edge(my_pin[name]['rising'])
        if has_falling_edge(my_pin[name]):
            pin_dict['falling'] = build_part_output_edge(my_pin[name]['falling'])
        data_pins.append(pin.new(pin_dict))
    return data_pins


def build_part_output_edge(edge_dict):
    edge = {}
    edge['max'] = {}
    edge['max']['id'] = edge_dict['clock_to_out_max']['id']
    edge['max']['value'] = edge_dict['clock_to_out_max']['value']
    edge['min'] = {}
    edge['min']['id'] = edge_dict['clock_to_out_min']['id']
    edge['min']['value'] = edge_dict['clock_to_out_min']['value']
    return edge


def build_device_interface(interface_dict):
    interface = DeviceInterface(interface_dict['name'])
    interface.output_clocks = build_output_clock_list(interface_dict)
    interface.input_clocks = build_input_clock_list(interface_dict)
    interface.internal_clocks = build_internal_clock_list(interface_dict)

    interface.data_pins = []
    interface.data_pins.extend(build_output_data_pin_list(interface_dict))
    interface.data_pins.extend(build_input_data_pin_list(interface_dict))

    return interface


def build_internal_clock_list(interface_dict):
    if 'internal' not in interface_dict['clock']:
        return None

    clock_pins = []
    for clock_pin in interface_dict['clock']['internal']:
        name = list(clock_pin.keys())[0]
        my_clock_pin = clock_pin[name]
        my_clock_pin['name'] = name
        my_clock_pin['pin_type'] = 'clock'
        my_clock_pin['location'] = 'device'
        my_clock_pin['direction'] = 'internal'
        new_clock_pin = pin.new(my_clock_pin)
        clock_pins.append(new_clock_pin)

    return clock_pins


def build_output_clock_list(interface_dict):
    if 'output' not in interface_dict['clock']:
        return None

    clock_pins = []
    for clock_pin in interface_dict['clock']['output']:
        name = list(clock_pin.keys())[0]
        my_clock_pin = clock_pin[name]
        my_clock_pin['name'] = name
        my_clock_pin['pin_type'] = 'clock'
        my_clock_pin['location'] = 'device'
        my_clock_pin['direction'] = 'output'
        new_clock_pin = pin.new(my_clock_pin)
        clock_pins.append(new_clock_pin)

    return clock_pins


def build_input_clock_list(interface_dict):
    if 'input' not in interface_dict['clock']:
        return None

    clock_pins = []
    for clock_pin in interface_dict['clock']['input']:
        name = list(clock_pin.keys())[0]
        my_clock_pin = clock_pin[name]
        my_clock_pin['name'] = name
        my_clock_pin['pin_type'] = 'clock'
        my_clock_pin['location'] = 'device'
        my_clock_pin['direction'] = 'input'
        new_clock_pin = pin.new(my_clock_pin)
        clock_pins.append(new_clock_pin)

    return clock_pins


def build_output_data_pin_list(interface_dict):
    if 'output' not in interface_dict['data']:
        return []

    data_pins = []

    for data_pin in interface_dict['data']['output']:
        name = list(data_pin.keys())[0]
        my_data_pin = data_pin[name]
        my_data_pin['name'] = name
        my_data_pin['pin_type'] = 'data'
        my_data_pin['location'] = 'device'
        my_data_pin['direction'] = 'output'
        new_data_pin = pin.new(my_data_pin)
        data_pins.append(new_data_pin)

    return data_pins


def build_input_data_pin_list(interface_dict):
    if 'input' not in interface_dict['data']:
        return []

    data_pins = []

    for data_pin in interface_dict['data']['input']:
        name = list(data_pin.keys())[0]
        my_data_pin = data_pin[name]
        my_data_pin['name'] = name
        my_data_pin['pin_type'] = 'data'
        my_data_pin['location'] = 'device'
        my_data_pin['direction'] = 'input'
        new_data_pin = pin.new(my_data_pin)
        data_pins.append(new_data_pin)

    return data_pins


class Interface():

    def __init__(self, name):
        self.name = name


class PartInterface(Interface):

    def __init__(self, name):
        Interface.__init__(self, name)
        self.timing_model = None
        self.clocks = None

    def has_pin_named(self, pin_name):
        if self.has_clock_pin_named(pin_name):
            return True
        if self.has_data_pin_named(pin_name):
            return True
        return False

    def has_data_pin_named(self, pin_name):
        for data_pin in self.data_pins:
            if data_pin.name == pin_name:
                return True
        return False

    def has_clock_pin_named(self, pin_name):
        for clock_pin in self.clocks:
            if clock_pin.name == pin_name:
                return True
        return False


class DeviceInterface(Interface):

    def __init__(self, name):
        Interface.__init__(self, name)
        self.input_clocks = None
        self.output_clocks = None
        self.internal_clocks = None
        self.data_pins = None

    def get_pin_named(self, pin_name):
        for data_pin in self.data_pins:
            if data_pin.name == pin_name:
                return data_pin
        for clock_pin in self.internal_clocks:
            if clock_pin.name == pin_name:
                return clock_pin
        for clock_pin in self.output_clocks:
            if clock_pin.name == pin_name:
                return clock_pin

    def get_clock_named(self, clock_name):
        for clock_pin in self.internal_clocks:
            if clock_pin.name == clock_name:
                return clock_pin
        for clock_pin in self.output_clocks:
            if clock_pin.name == clock_name:
                return clock_pin
        
