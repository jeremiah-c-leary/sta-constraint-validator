'''
:Stage: 0 - inputs
:Applies to: all
:Reads: type of every timing report (setup or hold), ``process_corner``
:Depends on: none

Setup timing reports must exist for at least two process corners.
The parser rejects a file with no timing reports, but a file with setup timing reports for only one process corner is valid.
Rules in stage 2 compare setup timing reports across process corners.
With fewer than two process corners, they have nothing to compare and would pass without checking anything.

**Violation**

Setup timing reports exist for the Fast process corner only:

.. code-block:: text
   :emphasize-lines: 2

     Slack (MET) :              7.192ns  (required time - arrival time)
       Path Type:              Max at Fast Process Corner

**Result**

The rule checks all timing reports together and gives one result.
When it fails, it lists the file and line of each setup timing report it found, with its process corner:

.. code-block:: text

     O_DAC_DATA_timing.rpt:75  setup timing report, Fast process corner

**Likely causes**

* The ``report_timing`` command was run for one process corner only.
* The setup timing reports for the other process corner were written to a different file than the one given to stacv.

Refer to the vendor's timing analysis documentation for reporting timing at multiple process corners.
'''

from stacv.rules import rule_result

RULE_ID = 's0_timing_report_001'


def check(oTimingReportList):
    '''
    Purpose:  Checks there are at least two setup timing reports at different process corners.
    '''

    lSetupTimingReports = oTimingReportList.get_setup_reports()
    lCorners = get_unique_timing_corners_from_reports(lSetupTimingReports)
    if at_least_two_corners_exist(lCorners):
        return rule_result.RuleResult(RULE_ID, rule_result.PASSED, [])
    lDetails = create_rule_result_detail(lSetupTimingReports)
    return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetails)


def get_unique_timing_corners_from_reports(lTimingReports):
    lCorners = []
    for oTimingReport in lTimingReports:
        sProcessCorner = oTimingReport.process_corner
        if sProcessCorner not in lCorners:
            lCorners.append(oTimingReport.process_corner)
    return lCorners


def at_least_two_corners_exist(lCorners):
    return len(lCorners) >= 2


def create_rule_result_detail(lTimingReports):
    lDetails = []
    for oTimingReport in lTimingReports:
        sFilename = oTimingReport.get_filename()
        iLineNumber = oTimingReport.get_first_line_number()
        sProcessCorner = oTimingReport.process_corner
        lDetails.append(f'{sFilename}:{iLineNumber}  setup timing report, {sProcessCorner} process corner')
    return lDetails
