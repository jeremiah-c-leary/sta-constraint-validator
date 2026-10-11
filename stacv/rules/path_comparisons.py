'''
Provides functions to compare DelayPath objects.
'''

from stacv.rules import rule_result


def check_paths_match(lReports, sPathType, sRuleId):
    lUniquePaths = identify_unique_paths(lReports, sPathType)
    if less_than_two_unique_paths(lUniquePaths):
        return rule_result.RuleResult(sRuleId, True, [])
    else:
        lDetails = create_path_details(lReports, lUniquePaths, sPathType)
        return rule_result.RuleResult(sRuleId, False, lDetails)


def identify_unique_paths(lReports, sPathType):
    lUniquePaths = []
    for oTimingReport in lReports:
        lPathResources = get_path_resources(oTimingReport, sPathType)
        add_path_to_list_if_new(lUniquePaths, lPathResources)
    return lUniquePaths


def add_path_to_list_if_new(lPaths, lResources):
    for lPath in lPaths:
        if lPath == lResources:
            return
    lPaths.append(lResources)


def less_than_two_unique_paths(lUniquePaths):
    return len(lUniquePaths) <= 1


def create_path_details(lReports, lUniquePaths, sPathType):
    lDetails = []
    for oReport in lReports:
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
