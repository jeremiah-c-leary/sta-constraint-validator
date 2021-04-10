
def new(interface_name, device, board, part):

    device_interface = get_device_interface_named(device, interface_name)
    part_interface = get_part_interface(device_interface, board, part)

    timing_model = build_timing_model(device_interface, board, part_interface, device, part)

    return timing_model


def get_device_interface_named(device, interface_name):
    return device.get_interface_named(interface_name)


def get_part_interface(device_interface, board, part):
    clock_pin = get_device_clock_pin(device_interface)
    part_clock_pin_name = board.get_part_pin_name_connected_to(clock_pin.name)
    part_interface = part.get_interface_with_pin_named(part_clock_pin_name)
    return part_interface


def get_device_clock_pin(device_interface):
    if device_interface.output_clocks is not None:
        return device_interface.output_clocks[0]


def build_timing_model(device_interface, board, part_interface, device, part):
    timing_model = SourceSynchronousWithRoundTrip(device_interface, board, part_interface)
    timing_model.device_name = device.name
    timing_model.part_name = part.name
    return timing_model


class TimingModel():

    def __init__(self, device_interface, traces, part_interface):
        self.device_interface = device_interface
        self.traces = traces
        self.part_interface = part_interface
        self.part_name = None

    def get_device_pin(self, pin_name):
        return self.device_interface.get_pin_named(pin_name)

    def get_device_clock_named(self, clock_name):
        return self.device_interface.get_clock_named(clock_name)


class SourceSynchronousWithRoundTrip(TimingModel):

    def __init__(self, device_interface, traces, part_interface):
        TimingModel.__init__(self, device_interface, traces, part_interface)
