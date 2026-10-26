'''
Contains functions to calculate output delays from the traces and part definitions.
'''

from stacv.rules import path_lookups


def calculate_expected_max_output_delay(oPortProfile):
    oDataTrace = path_lookups.get_data_trace(oPortProfile)
    oPartPin = path_lookups.get_part_pin_at_end_of_trace(oPortProfile, oDataTrace)
    oClockTrace = path_lookups.get_clock_trace(oPortProfile, oPartPin)
    return calculate_max_output_delay(oDataTrace, oPartPin, oClockTrace)


def calculate_max_output_delay(oDataTrace, oPartPin, oClockTrace):
    fMaxTraceDataDelay = oDataTrace.device_to_part.max_delay
    fMinTraceClockDelay = oClockTrace.device_to_part.min_delay
    fSetup = oPartPin.setup.value
    fMaxOutputDelay = fSetup + fMaxTraceDataDelay - fMinTraceClockDelay
    return fMaxOutputDelay


def calculate_expected_min_output_delay(oPortProfile):
    oDataTrace = path_lookups.get_data_trace(oPortProfile)
    oPartPin = path_lookups.get_part_pin_at_end_of_trace(oPortProfile, oDataTrace)
    oClockTrace = path_lookups.get_clock_trace(oPortProfile, oPartPin)
    return calculate_min_output_delay(oDataTrace, oPartPin, oClockTrace)


def calculate_min_output_delay(oDataTrace, oPartPin, oClockTrace):
    fMinTraceDataDelay = oDataTrace.device_to_part.min_delay
    fMaxTraceClockDelay = oClockTrace.device_to_part.max_delay
    fHold = oPartPin.hold.value
    fMinOutputDelay = -fHold + fMinTraceDataDelay - fMaxTraceClockDelay
    return fMinOutputDelay
