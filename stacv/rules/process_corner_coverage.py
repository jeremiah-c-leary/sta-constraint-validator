'''
Provides functions to check the coverage of timing reports.
'''

from stacv.results import rule_result
from stacv.rules import rule_details


def check_at_least_two_process_corners_exist(sRuleId, lTimingReports, sType, sFailureMessage):
    lCorners = get_unique_timing_corners_from_reports(lTimingReports)
    if at_least_two_corners_exist(lCorners):
        return rule_result.RuleResult(sRuleId, rule_result.PASSED, [], '')
    lDetails = create_rule_result_detail(lTimingReports, sType)
    return rule_result.RuleResult(sRuleId, rule_result.FAILED, lDetails, sFailureMessage)


def get_unique_timing_corners_from_reports(lTimingReports):
    lCorners = []
    for oTimingReport in lTimingReports:
        sProcessCorner = oTimingReport.process_corner
        if sProcessCorner not in lCorners:
            lCorners.append(oTimingReport.process_corner)
    return lCorners


def at_least_two_corners_exist(lCorners):
    return len(lCorners) >= 2


def create_rule_result_detail(lTimingReports, sType):
    lDetails = []
    for oTimingReport in lTimingReports:
        oFirstLine = oTimingReport.get_lines()[0]
        sMessage = f'{sType} timing report, {oTimingReport.process_corner} process corner'
        lDetails.append(rule_details.format_detail(oFirstLine, sMessage))
    return lDetails
