'''
This module includes functions to perform output delay comparisons.
'''


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
