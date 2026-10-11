'''
Provides functions to compare DelayPath objects.
'''

from stacv.rules import rule_result


def at_most_one_unique_delay_path_exists(oTimingReportList, sPathType, sRuleId):
    lAllReports = oTimingReportList.reports
    lUniquePaths = identify_unique_paths(lAllReports, sPathType)
    return check_paths_match(lAllReports, lUniquePaths, sPathType, sRuleId)


def identify_unique_paths(lAllReports, sPathType):
    lUniquePaths = []
    for oTimingReport in lAllReports:
        lPathResources = get_path_resources(oTimingReport, sPathType)
        add_path_to_list_if_new(lUniquePaths, lPathResources)
    return lUniquePaths


def add_path_to_list_if_new(lPaths, lResources):
    for lPath in lPaths:
        if lPath == lResources:
            return
    lPaths.append(lResources)


def check_paths_match(lAllReports, lUniquePaths, sPathType, sRuleId):
    if less_than_two_unique_paths(lUniquePaths):
        return rule_result.RuleResult(sRuleId, True, [])
    else:
        lDetails = create_path_details(lAllReports, lUniquePaths, sPathType)
        return rule_result.RuleResult(sRuleId, False, lDetails)


def less_than_two_unique_paths(lUniquePaths):
    return len(lUniquePaths) <= 1


def create_path_details(lAllReports, lUniquePaths, sPathType):
    lDetails = []
    for oReport in lAllReports:
        oPath = get_path(oReport, sPathType)
        iLabel = lUniquePaths.index(oPath.get_resources()) + 1
        oLine = oPath.first_line
        sDetail = f'{oLine.filename}:{oLine.line_number}  path {iLabel}'
        lDetails.append(sDetail)
    return lDetails


def get_path(oTimingReport, sPathType):
    return getattr(oTimingReport, sPathType)


def get_path_resources(oTimingReport, sPathType):
    return get_path(oTimingReport, sPathType).get_resources()
