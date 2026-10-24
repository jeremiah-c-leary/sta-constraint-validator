
def get_data_trace(oPortProfile):
    sPortName = oPortProfile.port.name
    return oPortProfile.traces.get_device_to_part_trace_starting_with_name(sPortName)


def get_part_pin_at_end_of_trace(oPortProfile, oDataTrace):
    return oPortProfile.part.get_pin_named(oDataTrace.part_pin)


def get_clock_trace(oPortProfile, oPartPin):
    sPartClockName = oPartPin.clock.pin
    sDeviceClockName = oPortProfile.port.capture_clock.port
    return oPortProfile.traces.get_device_to_part_trace_between(sDeviceClockName, sPartClockName)
