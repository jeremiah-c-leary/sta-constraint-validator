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

from stacv.rules import clock_comparisons
from stacv.rules import rule_details


RULE_ID = 's0_clock_path_001'
FAILURE_MESSAGE = 'Capture clock path in timing reports does not end at the configured clock port.'


def check(oPortProfile):
    '''
    Purpose:  Compares the last element of the capture clock path in the timing reports to the configured clock port.
    '''
    lDetails = get_capture_clock_path_end_mismatches(oPortProfile)

    return clock_comparisons.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_capture_clock_path_end_mismatches(oPortProfile):
    sClockPortName = oPortProfile.port.capture_clock.port
    lDetails = []
    for oTimingReport in oPortProfile.timing_reports.reports:
        oCaptureClockPathEnd = oTimingReport.capture_clock_path.get_last_delay()
        if oCaptureClockPathEnd.resource != sClockPortName:
            sErrorMessage = generate_error_message(oCaptureClockPathEnd, sClockPortName)
            lDetails.append(sErrorMessage)
    return lDetails


def generate_error_message(oCaptureClockPathEnd, sClockPortName):
    sMessage = f'capture clock path ends at {oCaptureClockPathEnd.resource}, configured clock port {sClockPortName}'
    return rule_details.format_detail(oCaptureClockPathEnd.line, sMessage)
