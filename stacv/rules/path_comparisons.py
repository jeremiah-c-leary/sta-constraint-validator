'''
Provides functions to compare DelayPath objects.
'''

from stacv.rules import rule_result


def at_most_one_unique_delay_path_exists(oTimingReportList, sPathType, sRuleId):
    lDelayPaths = identify_unique_paths(oTimingReportList, sPathType)
    return has_at_most_one_unique_path(lDelayPaths, sRuleId)


def identify_unique_paths(oTimingReportList, sPathType):
    lPaths = []
    for oTimingReport in oTimingReportList.reports:
        oPath = get_path(oTimingReport, sPathType)
        group_paths(lPaths, oPath)
    return lPaths


def group_paths(lPaths, oPath):
    iMaxIndex = 0
    for lPath in lPaths:
        iMaxIndex = max([iMaxIndex, lPath[1]])
        if path_resources_match(lPath[0], oPath):
            lPaths.append([oPath , lPath[1]])
            return
    lPaths.append([oPath, iMaxIndex + 1])


def path_resources_match(oPath1, oPath2):
    return oPath1.get_resources() == oPath2.get_resources()


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
