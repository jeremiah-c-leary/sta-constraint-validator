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

from stacv.rules import process_corner_coverage

RULE_ID = 's0_timing_report_001'
FAILURE_MESSAGE = 'Setup timing reports missing in at least one process corner.'


def check(oTimingReportList):
    '''
    Purpose:  Checks there are at least two setup timing reports at different process corners.
    '''

    lSetupTimingReports = oTimingReportList.get_setup_reports()
    return process_corner_coverage.check_at_least_two_process_corners_exist(RULE_ID, lSetupTimingReports, 'setup', FAILURE_MESSAGE)
