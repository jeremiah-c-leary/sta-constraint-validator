'''
:Stage: 3 - board and part
:Applies to: SDR-SS-RT
:Reads: ``input_delay`` of every setup timing report, trace delays, and part cko_max value
:Depends on: s2_input_delay_001

The maximum input delay in the timing reports must match the expected input delay.
This rule uses information from the user provided traces and part TOML files to calculate the maximum input delay.
The input delay in setup reports is then compared to the calculated value.
If it differs, then the values in the TOML files or the applied timing constraints are incorrect.

The calculation performed is: clock trace maximum delay + part clock to out maximum (``cko_max``) + data trace maximum delay.
The forwarded clock reaches the part, the part launches the data, and the data returns to the device.

The input delay matches when it is within 0.0005 ns of the calculated input delay, half of the last digit printed in the timing report.

**Result**

When the rule fails, it gives the file and line of the input delay of the first setup timing report:

.. code-block:: text

     I_DAC_DATA_timing.rpt:24  Calculated maximum input delay is 35.000ns while actual input delay is 34.000ns

**Likely causes**

* The trace delay values in the traces TOML file are incorrect
* The clock to out values in the part TOML file are incorrect
* The wrong input delay value was applied in the timing constraints

Refer to the vendor's timing constraints documentation for input delays.
'''

from stacv.results import rule_result
from stacv.rules import input_delays
from stacv.rules import rule_details
from stacv.rules import tolerance


RULE_ID = 's3_input_delay_001'
FAILURE_MESSAGE = 'Maximum input delay values in timing reports do not match delays in traces and part definitions.'
TOLERANCE = 0.0005


def check(oPortProfile):
    '''
    Purpose:  Check maximum input delay values match between configuration and timing reports.
    '''

    fActualInputDelay = get_first_setup_report(oPortProfile).input_delay
    fExpectedInputDelay = input_delays.calculate_expected_max_input_delay(oPortProfile)
    if tolerance.is_within_tolerance(fExpectedInputDelay, fActualInputDelay, TOLERANCE):
        return rule_result.RuleResult(RULE_ID, rule_result.PASSED, [], '')
    return generate_error_result(fActualInputDelay, fExpectedInputDelay, oPortProfile)


def get_first_setup_report(oPortProfile):
    '''
    A previous rule ensures all input delays are identical.
    Therefore, any report can be returned.
    '''
    return oPortProfile.timing_reports.get_setup_reports()[0]


def generate_error_result(fActualInputDelay, fExpectedInputDelay, oPortProfile):
    lDetails = []
    oInputDelayLine = get_first_setup_report(oPortProfile).input_delay_line
    sMessage = f'Calculated maximum input delay is {fExpectedInputDelay:.3f}ns while actual input delay is {fActualInputDelay:.3f}ns'
    lDetails.append(rule_details.format_detail(oInputDelayLine, sMessage))
    return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetails, FAILURE_MESSAGE)
