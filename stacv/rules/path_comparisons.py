'''
Provides functions to compare DelayPath objects.
'''

from stacv.rules import rule_result


def at_most_one_unique_delay_path_exists(oTimingReportList, sPathType, sRuleId):
    lDelayPaths = group_unique_delay_paths(oTimingReportList, sPathType)
    return has_at_most_one_unique_path(lDelayPaths, sRuleId)


def group_unique_delay_paths(oTimingReportList, sPathType):
    lUniquePaths = []
    for oTimingReport in oTimingReportList.reports:
        oPath = get_path(oTimingReport, sPathType)
        group_paths(lUniquePaths, oPath)
    return lUniquePaths


def group_paths(lUniquePaths, oPath):

    iMaxIndex = 0
    if len(lUniquePaths) == 0:
        lUniquePaths.append([oPath, 1])
        return
    for lPath in lUniquePaths:
        iMaxIndex = max([iMaxIndex, lPath[1]])
        if lPath[0].get_resources() == oPath.get_resources():
            lUniquePaths.append([oPath , lPath[1]])
            return
    lUniquePaths.append([oPath, iMaxIndex + 1])


def get_all_delay_paths(oTimingReportList, sPathType):
    lAllPaths = []
    for oTimingReport in oTimingReportList.reports:
        lResources = get_path_resources(oTimingReport, sPathType)
        lAllPaths.append(lResources)
    return lAllPaths


def has_at_most_one_unique_path(lUniquePaths, sRuleId):
    if less_than_two_unique_paths(lUniquePaths):
        return rule_result.RuleResult(sRuleId, True, [])
    else:
        return create_failing_rule_result(lUniquePaths, sRuleId)


def less_than_two_unique_paths(lUniquePaths):
    if len(lUniquePaths) == 0:
        return True
    for lPath in lUniquePaths:
        if lPath[1] > 1:
            return False
    return True


def create_failing_rule_result(lUniquePaths, sRuleId):
    lDetail = []
    for lPath in lUniquePaths:
        oLine = lPath[0].first_line
        iIndex = lPath[1]
        sDetail = f'{oLine.filename}:{oLine.line_number}  path {iIndex}'
        lDetail.append(sDetail)
    return rule_result.RuleResult(sRuleId, False, lDetail)


def get_path(oTimingReport, sPathType):
    return getattr(oTimingReport, sPathType)


def is_new_path(lResources, lUniquePaths):
    return lResources not in lUniquePaths
