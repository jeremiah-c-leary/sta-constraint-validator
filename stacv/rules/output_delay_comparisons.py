'''
This module includes functions to assist in output delay comparisons.

It includes functions the perform:
   * Comparisons of output delays across timing reports
   * Formatting of error reporting if output delays are not equal
'''

from stacv.results import rule_result
from stacv.rules import rule_details


def output_delays_are_identical(lReports):
    lUniqueOutputDelays = collect_unique_output_delays(lReports)
    return has_at_most_one_value(lUniqueOutputDelays)


def collect_unique_output_delays(lReports):
    lUniqueOutputDelays = []
    for oReport in lReports:
        if oReport.output_delay not in lUniqueOutputDelays:
            lUniqueOutputDelays.append(oReport.output_delay)
    return lUniqueOutputDelays


def has_at_most_one_value(lUniqueOutputDelays):
    return len(lUniqueOutputDelays) <= 1


def check_output_delays_match(lReports, sRuleId, sFailureMessage):
    if output_delays_are_identical(lReports):
        oRuleResult = rule_result.RuleResult(sRuleId, rule_result.PASSED, [], '')
    else:
        lDetails = create_output_delay_error_detail(lReports)
        oRuleResult = rule_result.RuleResult(sRuleId, rule_result.FAILED, lDetails, sFailureMessage)
    return oRuleResult


def create_output_delay_error_detail(lReports):
    lDetails = []
    for oReport in lReports:
        sDetail = format_detail_information(oReport)
        lDetails.append(sDetail)
    return lDetails


def format_detail_information(oReport):
    oOutputDelayLine = oReport.output_delay_line
    fDelay = oReport.output_delay
    return rule_details.format_detail(oOutputDelayLine, f'{fDelay:.3f}ns')
