
def new(device_interface, board, part):

    clock_pin = device_interface.external_clock
    device_clock_pin_name = board.get_part_pin_name_connected_to(clock_pin.name)
    part_interface = part.get_interface_with_pin_named(device_clock_pin_name)

    return SourceSynchronousWithRoundTrip(device_interface, board, part_interface)


class TimingModel():

    def __init__(self, device_interface, traces, part_interface):
        self.device_interface = device_interface
        self.traces = traces
        self.part_interface = part_interface


class SourceSynchronousWithRoundTrip(TimingModel):

    def __init__(self, device_interface, traces, part_interface):
        TimingModel.__init__(self, device_interface, traces, part_interface)

