'''
Contains functions to calculate input delays from the traces and part definitions.
'''

from stacv.rules import path_lookups


def calculate_expected_max_input_delay(oPortProfile):
    oDataTrace, oPartPin, oClockTrace = find_input_delay_inputs(oPortProfile)
    return calculate_max_input_delay(oDataTrace, oPartPin, oClockTrace)


def calculate_max_input_delay(oDataTrace, oPartPin, oClockTrace):
    # The forwarded clock reaches the part, the part launches the data, and the data returns to the device.
    fMaxTraceClockDelay = oClockTrace.device_to_part.max_delay
    fMaxClockToOut = oPartPin.cko_max.value
    fMaxTraceDataDelay = oDataTrace.part_to_device.max_delay
    return fMaxTraceClockDelay + fMaxClockToOut + fMaxTraceDataDelay


def calculate_expected_min_input_delay(oPortProfile):
    oDataTrace, oPartPin, oClockTrace = find_input_delay_inputs(oPortProfile)
    return calculate_min_input_delay(oDataTrace, oPartPin, oClockTrace)


def calculate_min_input_delay(oDataTrace, oPartPin, oClockTrace):
    fMinTraceClockDelay = oClockTrace.device_to_part.min_delay
    fMinClockToOut = oPartPin.cko_min.value
    fMinTraceDataDelay = oDataTrace.part_to_device.min_delay
    return fMinTraceClockDelay + fMinClockToOut + fMinTraceDataDelay


def find_input_delay_inputs(oPortProfile):
    oDataTrace = path_lookups.get_input_data_trace(oPortProfile)
    oPartPin = path_lookups.get_part_pin_at_end_of_trace(oPortProfile, oDataTrace)
    oClockTrace = path_lookups.get_clock_trace(oPortProfile, oPartPin)
    return oDataTrace, oPartPin, oClockTrace
