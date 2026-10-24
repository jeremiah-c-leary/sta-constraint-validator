'''
:Stage: 0 - inputs
:Applies to: SDR-SS-O
:Reads: last element of the capture clock path of every timing report, ``capture_clock.port`` of the port in the configuration
:Depends on: none

The capture clock path of every timing report of a port must end at the configured clock port.
Every timing report is checked, setup and hold, at every process corner.
The last element of the capture clock path is the net to the clock port, which the timing tool names after the port.
If the capture clock path ends anywhere else, the timing report times the data against a different clock, and the results of the other rules do not apply to the port.

**Violation**

The port is configured with ``capture_clock = {port = "O_DAC_CSF", ...}``, but the capture clock path of the timing report ends at ``O_DAC_SCLK``:

.. code-block:: text
   :emphasize-lines: 1

                            net (fo=0)                   0.000     3.959    O_DAC_SCLK
       U15                                                               r  O_DAC_SCLK (OUT)

**Result**

When the rule fails, it lists each timing report whose capture clock path ends somewhere else, with the file and line of the last element of the capture clock path:

.. code-block:: text

     O_DAC_DATA_timing.rpt:65  capture clock path ends at O_DAC_SCLK, configured clock port O_DAC_CSF

**Likely causes**

* The clock port in the configuration is wrong.
* The output delay constraint refers to a clock that is not forwarded on the clock port.
* The wrong timing report is listed under the port.
'''

from stacv.results import rule_result
from stacv.rules import rule_details


RULE_ID = 's0_clock_path_001'
FAILURE_MESSAGE = 'Capture clock path in timing reports does not end at the configured clock port.'


def check(oPortProfile):
    '''
    Purpose:  Compares the last element of the capture clock path in the timing reports to the configured clock port.
    '''
    lMismatchedTimingReports = get_mismatched_timing_reports(oPortProfile.timing_reports.reports, oPortProfile.port)
    lDetails = generate_error_messages(lMismatchedTimingReports, oPortProfile.port)

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_mismatched_timing_reports(lTimingReports, oPort):
    lMismatchedTimingReports = []
    for oTimingReport in lTimingReports:
        if capture_clock_path_ends_elsewhere(oTimingReport, oPort):
            lMismatchedTimingReports.append(oTimingReport)
    return lMismatchedTimingReports


def capture_clock_path_ends_elsewhere(oTimingReport, oPort):
    return get_capture_clock_path_end(oTimingReport).resource != oPort.capture_clock.port


def generate_error_messages(lTimingReports, oPort):
    lDetails = []
    for oTimingReport in lTimingReports:
        sErrorMessage = generate_error_message(oTimingReport, oPort)
        lDetails.append(sErrorMessage)
    return lDetails


def generate_error_message(oTimingReport, oPort):
    oCaptureClockPathEnd = get_capture_clock_path_end(oTimingReport)
    sMessage = f'capture clock path ends at {oCaptureClockPathEnd.resource}, configured clock port {oPort.capture_clock.port}'
    return rule_details.format_detail(oCaptureClockPathEnd.line, sMessage)


def get_capture_clock_path_end(oTimingReport):
    return oTimingReport.capture_clock_path.get_last_delay()
