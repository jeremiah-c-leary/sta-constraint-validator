'''
:Stage: 3 - across timing reports
:Applies to: SDR-SS-O, DDR-SS-O
:Reads: ``output_delay`` of every setup timing report
:Depends on: none

The maximum output delay in the timing reports must match the expected output delay.
This rule uses information from the user provided traces and port TOML files to calculate the maximum output delay.
The output delay in setup reports is then compared to the calculate value.
If it differs, then the values in the TOML files or the applied timing contraints are incorrect.

The calculation performed is: part setup + data trace maximum delay - clock trace minimum delay.

The output delay matches when it is within 0.0005 ns of the calculated output delay, half of the last digit printed in the timing report.

**Likely causes**

* The trace delay values in the traces TOML file are incorrect
* The constraint values in the part TOML file are incorrect
* The wrong output delay value was applied in the timing constraints

Refer to the vendor's timing constraints documentation for output delays.
'''

from stacv.rules import output_delay_comparisons
from stacv.results import rule_result


RULE_ID = 's3_output_delay_001'
FAILURE_MESSAGE = 'Maximum output delay value in timing reports do not match delays in traces and part definitions.'
TOLERANCE = 0.0005


def check(oPortProfile):
    '''
    Purpose:  Check output delay values match between configuration and timing reports.
    '''

    fActualOutputDelay = get_output_delay_from_setup_reports(oPortProfile)
    fExpectedOutputDelay = calculate_expected_max_output_delay(oPortProfile)
    if output_delay_in_range(fActualOutputDelay, fExpectedOutputDelay):
        return rule_result.RuleResult(RULE_ID, rule_result.PASSED)
    return generate_error_result(fExpectedOutputDelay, fActualOutputDelay)


def get_output_delay_from_setup_reports(oPortProfile):
    '''
    A previous rule ensures all output delays are identical.
    Therefore, any output delay can be returned.
    '''
    lSetupReports = oPortProfile.timing_reports.get_setup_reports()
    return lSetupReports[0].output_delay


def calculate_expected_max_output_delay(oPortProfile):
    oDataTrace = get_data_trace(oPortProfile)
    oPartPin = get_part_data_pin(oPortProfile, oDataTrace)
    oClockTrace = get_clock_trace(oPortProfile, oPartPin)
    return calculate_max_output_delay(oDataTrace, oPartPin, oClockTrace)


def get_data_trace(oPortProfile):
    sPortName = oPortProfile.port.name
    return oPortProfile.traces.get_trace_with_device_pin(sPortName)


def get_part_data_pin(oPortProfile, oDataTrace):
    return oPortProfile.part.get_pin_named(oDataTrace.part_pin)


def get_clock_trace(oPortProfile, oPartPin):
    sPartClockName = oPartPin.clock.pin
    return oPortProfile.traces.get_trace_with_part_pin(sPartClockName)


def calculate_max_output_delay(oDataTrace, oPartPin, oClockTrace):
    fMaxTraceDataDelay = oDataTrace.device_to_part.max_delay
    fMinTraceClockDelay = oClockTrace.device_to_part.min_delay
    fSetup = oPartPin.setup.value
    fMaxOutputDelay = fSetup + fMaxTraceDataDelay - fMinTraceClockDelay
    return fMaxOutputDelay


def output_delay_in_range(fActualOutputDelay, fExpectedOutputDelay):
    return fActualOutputDelay - TOLERANCE < fExpectedOutputDelay < fActualOutputDelay + TOLERANCE


def generate_error_result(fExpectedOutputDelay, fActualOutputDelay):
    lDetails = []
    lDetails.append(f'Calculated maximum output delay is {fExpectedOutputDelay} while actual output delay is {fActualOutputDelay}')
    return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetails, FAILURE_MESSAGE)
