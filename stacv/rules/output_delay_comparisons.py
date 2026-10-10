'''
This module includes functions to assist in output delay comparisons.

It includes functions the perform:
   * Comparisons of output delays across timing reports
   * Formatting of error reporting if output delays are not equal
'''

from stacv.rules import rule_result


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


def check_output_delays_match(lReports, sRuleId):
    if output_delays_are_identical(lReports):
        oRuleResult = rule_result.RuleResult(sRuleId, True, [])
    else:
        lDetails = create_output_delay_error_detail(lReports)
        oRuleResult = rule_result.RuleResult(sRuleId, False, lDetails)
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
    return f'{oOutputDelayLine.filename}:{oOutputDelayLine.line_number}  {fDelay:.3f}ns'
