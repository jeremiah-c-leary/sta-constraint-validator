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


def check(oPortProfile):
    '''
    Purpose:  Check output delay values match between configuration and timing reports.
    '''

    lSetupReports = oPortProfile.timing_reports.get_setup_reports()
    fActualOutputDelay = lSetupReports[0].output_delay
    fExpectedOutputDelay = calculate_expected_max_output_delay(oPortProfile)
    if fActualOutputDelay - 0.0005 < fExpectedOutputDelay < fActualOutputDelay + 0.0005:
        return rule_result.RuleResult(RULE_ID, rule_result.PASSED, '', FAILURE_MESSAGE)
    lDetails = []
    lDetails.append('Calculated maximum output delay is {fExpectedOutputDelay} while actual output delay is {fActualOutputDelay}')
    return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetails, FAILURE_MESSAGE)


def calculate_expected_max_output_delay(oPortProfile):
    sPortName = oPortProfile.port.name
    oDataTrace = oPortProfile.traces.get_trace_with_device_pin(sPortName)
    iMaxTraceDataDelay = oDataTrace.device_to_part.max_delay
    oPartPin = oPortProfile.part.get_pin_named(oDataTrace.part_pin)
    sPartClockName = oPartPin.clock.pin
    iSetup = oPartPin.setup.value
    oClockTrace = oPortProfile.traces.get_trace_with_part_pin(sPartClockName)
    iMinTraceClockDelay = oClockTrace.device_to_part.min_delay
    fMaxOutputDelay = iSetup + iMaxTraceDataDelay - iMinTraceClockDelay
    return fMaxOutputDelay
