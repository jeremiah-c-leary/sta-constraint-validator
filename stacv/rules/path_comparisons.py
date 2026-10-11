'''
Provides functions to compare DelayPath objects.
'''

from stacv.rules import rule_result


def at_most_one_unique_delay_path_exists(oTimingReportList, sPathType, sRuleId):
    lUniquePaths = identify_unique_paths(oTimingReportList, sPathType)
    lAllReports = oTimingReportList.reports
    return has_at_most_one_unique_path(lAllReports, lUniquePaths, sPathType, sRuleId)


def identify_unique_paths(oTimingReportList, sPathType):
    lUniquePaths = []
    for oTimingReport in oTimingReportList.reports:
        lPathResources = get_path_resources(oTimingReport, sPathType)
        uniquify_paths(lUniquePaths, lPathResources)
    return lUniquePaths


def uniquify_paths(lPaths, lResources):
    for lPath in lPaths:
        if lPath == lResources:
            return
    lPaths.append(lResources)


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


def get_path_resources(oTimingReport, sPathType):
    return get_path(oTimingReport, sPathType).get_resources()
