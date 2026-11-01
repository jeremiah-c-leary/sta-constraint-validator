
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
    return oPortProfile.part.get_pin_named(oDataTrace.part_pin)


def get_clock_trace(oPortProfile, oPartPin):
    sPartClockName = oPartPin.clock.pin
    sDeviceClockName = oPortProfile.port.forwarded_clock.port
    return oPortProfile.traces.get_device_to_part_trace_between(sDeviceClockName, sPartClockName)
