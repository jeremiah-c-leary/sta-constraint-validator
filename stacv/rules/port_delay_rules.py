'''
Compares the input or output delay in the timing reports with the delay calculated from the traces and the part,
for the stage 3 rules whose calculation is in port_delays.

A maximum delay is compared with a setup timing report, and a minimum delay with a hold timing report.
A previous rule ensures every setup, or every hold, timing report gives the same delay, so the first one is compared.
'''

from stacv.results import rule_result
from stacv.rules import port_delays
from stacv.rules import rule_details
from stacv.rules import tolerance

# Half of the last digit printed in the timing report.
TOLERANCE = 0.0005
INPUT_DELAY = 'input_delay'
OUTPUT_DELAY = 'output_delay'


def check_maximum_delay(oPortProfile, fnCalculate, sDelay, sRuleId, sFailureMessage):
    oTimingReport = oPortProfile.timing_reports.get_setup_reports()[0]
    oMaximum, oMinimum = fnCalculate(port_delays.Inputs(oPortProfile))
    return compare_delay(oTimingReport, oMaximum.value, sDelay, 'maximum', sRuleId, sFailureMessage)


def check_minimum_delay(oPortProfile, fnCalculate, sDelay, sRuleId, sFailureMessage):
    oTimingReport = oPortProfile.timing_reports.get_hold_reports()[0]
    oMaximum, oMinimum = fnCalculate(port_delays.Inputs(oPortProfile))
    return compare_delay(oTimingReport, oMinimum.value, sDelay, 'minimum', sRuleId, sFailureMessage)


def compare_delay(oTimingReport, fExpectedDelay, sDelay, sLimit, sRuleId, sFailureMessage):
    fActualDelay = getattr(oTimingReport, sDelay)
    if tolerance.is_within_tolerance(fExpectedDelay, fActualDelay, TOLERANCE):
        return rule_result.RuleResult(sRuleId, rule_result.PASSED, [], '')
    sName = sDelay.replace('_', ' ')
    sMessage = f'Calculated {sLimit} {sName} is {fExpectedDelay:.3f}ns while actual {sName} is {fActualDelay:.3f}ns'
    lDetails = [rule_details.format_detail(getattr(oTimingReport, sDelay + '_line'), sMessage)]
    return rule_result.RuleResult(sRuleId, rule_result.FAILED, lDetails, sFailureMessage)
