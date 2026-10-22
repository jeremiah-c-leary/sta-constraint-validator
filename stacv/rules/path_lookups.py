
def get_data_trace(oPortProfile):
    sPortName = oPortProfile.port.name
    return oPortProfile.traces.get_trace_with_device_pin(sPortName)


def get_part_data_pin(oPortProfile, oDataTrace):
    return oPortProfile.part.get_pin_named(oDataTrace.part_pin)


def get_clock_trace(oPortProfile, oPartPin):
    sPartClockName = oPartPin.clock.pin
    return oPortProfile.traces.get_trace_with_part_pin(sPartClockName)
