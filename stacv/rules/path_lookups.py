
def get_data_trace(oPortProfile):
    sPortName = oPortProfile.port.name
    return oPortProfile.traces.get_device_to_part_trace_starting_with_name(sPortName)


def get_part_data_pin(oPortProfile, oDataTrace):
    return oPortProfile.part.get_pin_named(oDataTrace.part_pin)


def get_clock_trace(oPortProfile, oPartPin):
    sPartClockName = oPartPin.clock.pin
    return oPortProfile.traces.get_device_to_part_trace_ending_with_name(sPartClockName)
