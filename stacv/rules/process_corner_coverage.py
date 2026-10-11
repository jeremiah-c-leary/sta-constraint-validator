'''
Provides functions to check the coverage of timing reports.
'''

from stacv.rules import rule_result


def check_at_least_two_process_corners_exist(sRuleId, lTimingReports, sType):
    lCorners = get_unique_timing_corners_from_reports(lTimingReports)
    if at_least_two_corners_exist(lCorners):
        return rule_result.RuleResult(sRuleId, rule_result.PASSED, [])
    lDetails = create_rule_result_detail(lTimingReports, sType)
    return rule_result.RuleResult(sRuleId, rule_result.FAILED, lDetails)


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
        sFilename = oTimingReport.get_filename()
        iLineNumber = oTimingReport.get_first_line_number()
        sProcessCorner = oTimingReport.process_corner
        lDetails.append(f'{sFilename}:{iLineNumber}  {sType} timing report, {sProcessCorner} process corner')
    return lDetails
