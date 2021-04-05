
def new(interface_name, device, board, part):

    device_interface = device.get_interface_named(interface_name)
    clock_pin = device_interface.external_clock
    device_clock_pin_name = board.get_part_pin_name_connected_to(clock_pin.name)
    part_interface = part.get_interface_with_pin_named(device_clock_pin_name)

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


class SourceSynchronousWithRoundTrip(TimingModel):

    def __init__(self, device_interface, traces, part_interface):
        TimingModel.__init__(self, device_interface, traces, part_interface)

