'''
This module includes functions to assist in output and input delay comparisons.

It includes functions the perform:
   * Comparisons of output or input delays across timing reports
   * Formatting of error reporting if the delays are not equal

The delay is named by its timing report attribute, output_delay or input_delay, whose line is the attribute with _line added.
'''

from stacv.results import rule_result
from stacv.rules import rule_details

OUTPUT_DELAY = 'output_delay'
INPUT_DELAY = 'input_delay'


def delays_are_identical(lReports, sDelay):
    lUniqueDelays = collect_unique_delays(lReports, sDelay)
    return has_at_most_one_value(lUniqueDelays)


def collect_unique_delays(lReports, sDelay):
    lUniqueDelays = []
    for oReport in lReports:
        fDelay = getattr(oReport, sDelay)
        if fDelay not in lUniqueDelays:
            lUniqueDelays.append(fDelay)
    return lUniqueDelays


def has_at_most_one_value(lUniqueDelays):
    return len(lUniqueDelays) <= 1


def check_delays_match(lReports, sDelay, sRuleId, sFailureMessage):
    if delays_are_identical(lReports, sDelay):
        oRuleResult = rule_result.RuleResult(sRuleId, rule_result.PASSED, [], '')
    else:
        lDetails = create_delay_error_detail(lReports, sDelay)
        oRuleResult = rule_result.RuleResult(sRuleId, rule_result.FAILED, lDetails, sFailureMessage)
    return oRuleResult


def create_delay_error_detail(lReports, sDelay):
    lDetails = []
    for oReport in lReports:
        sDetail = format_detail_information(oReport, sDelay)
        lDetails.append(sDetail)
    return lDetails


def format_detail_information(oReport, sDelay):
    oDelayLine = getattr(oReport, sDelay + '_line')
    fDelay = getattr(oReport, sDelay)
    return rule_details.format_detail(oDelayLine, f'{fDelay:.3f}ns')
