'''
Provides functions to compare DelayPath objects.
'''


def at_most_one_unique_delay_path_exists(oTimingReportList, sPathType):
    lUniquePaths = get_unique_delay_paths(oTimingReportList, sPathType)
    return has_at_most_one_path(lUniquePaths)


def get_unique_delay_paths(oTimingReportList, sPathType):
    lUniquePaths = []
    for oTimingReport in oTimingReportList.reports:
        lResources = get_path_resources(oTimingReport, sPathType)
        if is_new_path(lResources, lUniquePaths):
            lUniquePaths.append(lResources)
    return lUniquePaths


def has_at_most_one_path(lUniquePaths):
    return len(lUniquePaths) <= 1


def get_path_resources(oTimingReport, sPathType):
    return getattr(oTimingReport, sPathType).get_resources()


def is_new_path(lResources, lUniquePaths):
    return lResources not in lUniquePaths
