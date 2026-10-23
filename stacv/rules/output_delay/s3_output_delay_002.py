'''
:Stage: 3 - board and part
:Applies to: SDR-SS-O, DDR-SS-O
:Reads: ``output_delay`` of every hold timing report, trace delays, and part hold value
:Depends on: s2_output_delay_002

The minimum output delay in the timing reports must match the expected output delay.
This rule uses information from the user provided traces and part TOML files to calculate the minimum output delay.
The output delay in hold reports is then compared to the calculated value.
If it differs, then the values in the TOML files or the applied timing constraints are incorrect.

The calculation performed is:  - part hold + data trace minimum delay - clock trace maximum delay.

The output delay matches when it is within 0.0005 ns of the calculated output delay, half of the last digit printed in the timing report.

**Likely causes**

* The trace delay values in the traces TOML file are incorrect
* The constraint values in the part TOML file are incorrect
* The wrong output delay value was applied in the timing constraints

Refer to the vendor's timing constraints documentation for output delays.
'''

from stacv.results import rule_result
from stacv.rules import path_lookups


RULE_ID = 's3_output_delay_002'
FAILURE_MESSAGE = 'Minimum output delay values in timing reports do not match delays in traces and part definitions.'
TOLERANCE = 0.0005


def check(oPortProfile):
    '''
    Purpose:  Check minimum output delay values match between configuration and timing reports.
    '''

    fActualOutputDelay = get_output_delay_from_hold_reports(oPortProfile)
    fExpectedOutputDelay = calculate_expected_min_output_delay(oPortProfile)
    if output_delay_in_range(fActualOutputDelay, fExpectedOutputDelay):
        return rule_result.RuleResult(RULE_ID, rule_result.PASSED, [], '')
    return generate_error_result(fActualOutputDelay, fExpectedOutputDelay, oPortProfile)


def get_output_delay_from_hold_reports(oPortProfile):
    return get_first_hold_report(oPortProfile).output_delay


def get_first_hold_report(oPortProfile):
    '''
    A previous rule ensures all output delays are identical.
    Therefore, any report can be returned.
    '''
    lHoldReports = oPortProfile.timing_reports.get_hold_reports()
    return lHoldReports[0]


def calculate_expected_min_output_delay(oPortProfile):
    oDevicePin = oPortProfile.port.capture_clock
    oDataTrace = path_lookups.get_data_trace(oPortProfile)
    oPartPin = path_lookups.get_part_data_pin(oPortProfile, oDataTrace)
    oClockTrace = path_lookups.get_clock_trace(oPortProfile, oPartPin, oDevicePin)
    return calculate_min_output_delay(oDataTrace, oPartPin, oClockTrace)


def calculate_min_output_delay(oDataTrace, oPartPin, oClockTrace):
    fMinTraceDataDelay = oDataTrace.device_to_part.min_delay
    fMaxTraceClockDelay = oClockTrace.device_to_part.max_delay
    fHold = oPartPin.hold.value
    fMinOutputDelay = -fHold + fMinTraceDataDelay - fMaxTraceClockDelay
    return fMinOutputDelay


def output_delay_in_range(fActualOutputDelay, fExpectedOutputDelay):
    return fActualOutputDelay - TOLERANCE < fExpectedOutputDelay < fActualOutputDelay + TOLERANCE


def generate_error_result(fActualOutputDelay, fExpectedOutputDelay, oPortProfile):
    lDetails = []
    oOutputDelayLine = get_first_hold_report(oPortProfile).output_delay_line
    lDetails.append(f'{oOutputDelayLine.filename}:{oOutputDelayLine.line_number}  Calculated minimum output delay is {fExpectedOutputDelay:.3f}ns while actual output delay is {fActualOutputDelay:.3f}ns')
    return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetails, FAILURE_MESSAGE)
