'''
Provides functions to compare DelayPath objects.
'''

from stacv.rules import rule_result


def at_most_one_unique_delay_path_exists(oTimingReportList, sPathType, sRuleId):
    lUniquePaths = identify_unique_paths(oTimingReportList, sPathType)
    lAllReports = oTimingReportList.reports
    return has_at_most_one_unique_path(lAllReports, lUniquePaths, sPathType, sRuleId)


def identify_unique_paths(oTimingReportList, sPathType):
    lPaths = []
    for oTimingReport in oTimingReportList.reports:
        oPath = get_path(oTimingReport, sPathType)
        group_paths(lPaths, oPath)
    return lPaths


def group_paths(lPaths, oPath):
    for lPath in lPaths:
        if path_resources_match(lPath, oPath.get_resources()):
            return
    lPaths.append(oPath.get_resources())


def path_resources_match(lPath1, lPath2):
    return lPath1 == lPath2


def has_at_most_one_unique_path(lAllReports, lUniquePaths, sPathType, sRuleId):
    if less_than_two_unique_paths(lUniquePaths):
        return rule_result.RuleResult(sRuleId, True, [])
    else:
        return create_failing_rule_result(lAllReports, lUniquePaths, sPathType, sRuleId)


def less_than_two_unique_paths(lUniquePaths):
    return len(lUniquePaths) <= 1


def create_failing_rule_result(lAllReports, lUniquePaths, sPathType, sRuleId):
    lDetail = []
    for oReport in lAllReports:
        oPath = get_path(oReport, sPathType)
        iIndex = lUniquePaths.index(oPath.get_resources()) + 1
        oLine = oPath.first_line
        sDetail = f'{oLine.filename}:{oLine.line_number}  path {iIndex}'
        lDetail.append(sDetail)
    return rule_result.RuleResult(sRuleId, False, lDetail)


def get_path(oTimingReport, sPathType):
    return getattr(oTimingReport, sPathType)
