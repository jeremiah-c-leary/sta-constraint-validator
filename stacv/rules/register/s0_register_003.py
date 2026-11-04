'''
:Stage: 0 - inputs
:Applies to: all
:Reads: process corner and type of every timing report
:Depends on: none

The report script asks the timing tool for at most 100 paths in each report, for setup and hold at each process corner.
A report with 100 paths may have left paths out, so the other rules cannot be sure every register was seen.

**Result**

When the rule fails, it gives the file and line of the first path of each full report:

.. code-block:: text

     O_BUS_timing.rpt:14  100 setup paths at the Slow process corner, the most the report script asks for

**Likely causes**

* The port is a wide bus, or many registers drive or capture it; raise the limit in the report script.
'''

from stacv.results import rule_result
from stacv.rules import registers
from stacv.rules import rule_details


RULE_ID = 's0_register_003'
FAILURE_MESSAGE = 'A timing report has as many paths as the report script asks for, so it may have left paths out.'


def check(oPortProfile):
    '''
    Purpose:  No report reaches the most paths the report script asks for.
    '''
    lDetails = []
    for sType, lReports in [('setup', oPortProfile.timing_reports.get_setup_reports()), ('hold', oPortProfile.timing_reports.get_hold_reports())]:
        for sCorner, lCornerReports in group_by_corner(lReports):
            if len(lCornerReports) >= registers.PATH_LIMIT:
                sMessage = f'{len(lCornerReports)} {sType} paths at the {sCorner} process corner, the most the report script asks for'
                lDetails.append(rule_details.format_detail(lCornerReports[0].slack_line, sMessage))
    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def group_by_corner(lReports):
    lGroups = []
    dGroups = {}
    for oTimingReport in lReports:
        if oTimingReport.process_corner not in dGroups:
            dGroups[oTimingReport.process_corner] = []
            lGroups.append((oTimingReport.process_corner, dGroups[oTimingReport.process_corner]))
        dGroups[oTimingReport.process_corner].append(oTimingReport)
    return lGroups
