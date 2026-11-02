
from stacv.methodology import methodology


def get_port_data_trace(oPortProfile):
    # The data trace runs from the device to the part for an output, and from the part to the device for an input.
    if oPortProfile.port.data_direction == methodology.INPUT:
        return get_input_data_trace(oPortProfile)
    return get_data_trace(oPortProfile)


def get_data_trace(oPortProfile):
    sPortName = oPortProfile.port.name
    return oPortProfile.traces.get_device_to_part_trace_starting_with_name(sPortName)


def get_input_data_trace(oPortProfile):
    sPortName = oPortProfile.port.name
    return oPortProfile.traces.get_part_to_device_trace_ending_with_name(sPortName)


def get_part_data_pin(oPortProfile):
    oDataTrace = get_port_data_trace(oPortProfile)
    return get_part_pin_at_end_of_trace(oPortProfile, oDataTrace)


def get_part_pin_at_end_of_trace(oPortProfile, oDataTrace):
    # A bidirectional pin has a table for each direction, so the port's part pin methodology picks one.
    return oPortProfile.part.get_pin_named(oDataTrace.part_pin, oPortProfile.port.part_pin_methodology)


def get_clock_trace(oPortProfile, oPartPin):
    # The clock trace runs from the device to the part when the device forwards the clock, and from the part to the device when the part sends it.
    sPartClockName = oPartPin.clock.pin
    sDeviceClockName = oPortProfile.port.forwarded_clock.port
    if oPortProfile.port.clock_origin == methodology.PART_CLOCK:
        return oPortProfile.traces.get_part_to_device_trace_between(sPartClockName, sDeviceClockName)
    if oPortProfile.port.clock_origin == methodology.SOURCE_CLOCK:
        return get_source_to_device_clock_trace(oPortProfile)
    return oPortProfile.traces.get_device_to_part_trace_between(sDeviceClockName, sPartClockName)


def get_clock_trace_delay(oPortProfile, oClockTrace):
    if oPortProfile.port.clock_origin == methodology.PART_CLOCK:
        return oClockTrace.part_to_device
    if oPortProfile.port.clock_origin == methodology.SOURCE_CLOCK:
        return oClockTrace.source_to_device
    return oClockTrace.device_to_part


def get_source_to_device_clock_trace(oPortProfile):
    return oPortProfile.traces.get_source_to_device_trace_ending_with_name(oPortProfile.port.forwarded_clock.port)


def get_source_to_part_clock_trace(oPortProfile, oPartPin):
    # The source's other trace reaches the clock pin of the part pin.
    oDeviceClockTrace = get_source_to_device_clock_trace(oPortProfile)
    if oDeviceClockTrace is None:
        return None
    return oPortProfile.traces.get_source_to_part_trace(oDeviceClockTrace.source, oPartPin.clock.pin)


def get_data_trace_delay(oPortProfile, oDataTrace):
    if oPortProfile.port.data_direction == methodology.INPUT:
        return oDataTrace.part_to_device
    return oDataTrace.device_to_part
