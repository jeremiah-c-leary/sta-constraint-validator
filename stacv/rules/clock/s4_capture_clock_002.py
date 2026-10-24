'''
:Stage: 4 - configuration
:Applies to: all
:Reads: ``capture_clock`` period of every timing report, ``capture_clock.period`` of the port in the configuration
:Depends on: none

The period of the capture clock in every timing report must match the period configured for the port's capture clock.
Every timing report is checked, setup and hold, at every process corner.
The configured period is in nanoseconds.
The period matches when it is within 0.0005 ns of the configured period, half of the last digit printed in the timing report.
If the period differs, the setup and hold requirements are calculated for a clock the part does not receive.

**Violation**

The port is configured with ``capture_clock = {port = "O_DAC_SCLK", name = "dac_sclk", period = 20.000}``, but the timing report gives 40.000 ns:

.. code-block:: text
   :emphasize-lines: 2

     Destination:            O_DAC_DATA
                               (output port clocked by dac_sclk  {rise@0.000ns fall@20.000ns period=40.000ns})

**Result**

When the rule fails, it lists each timing report whose capture clock period differs, with the file and line of the capture clock:

.. code-block:: text

     O_DAC_DATA_timing.rpt:18  capture clock period 40.000ns, configured period 20.000ns

**Likely causes**

* The capture clock period in the configuration is wrong.
* The divide or multiply factor of the generated clock in the timing constraints is wrong.
* The period of the source clock in the timing constraints is wrong.

Refer to the vendor's timing constraints documentation for generated clocks.
'''

from stacv.results import rule_result
from stacv.rules import rule_details
from stacv.rules import tolerance


RULE_ID = 's4_capture_clock_002'
FAILURE_MESSAGE = 'Capture clock period in configuration does not match clock period in all timing reports.'
TOLERANCE = 0.0005


def check(oPortProfile):
    '''
    Purpose:  Compares the configuration capture clock period to the capture clock period in the timing reports.
    '''
    lMismatchedTimingReports = get_mismatched_timing_reports(oPortProfile.timing_reports.reports, oPortProfile.port)
    lDetails = generate_error_messages(lMismatchedTimingReports, oPortProfile.port)

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_mismatched_timing_reports(lTimingReports, oPort):
    lMismatchedTimingReports = []
    for oTimingReport in lTimingReports:
        if capture_clock_period_differs(oTimingReport, oPort):
            lMismatchedTimingReports.append(oTimingReport)
    return lMismatchedTimingReports


def capture_clock_period_differs(oTimingReport, oPort):
    return not tolerance.is_within_tolerance(oPort.capture_clock.period, oTimingReport.capture_clock.period, TOLERANCE)


def generate_error_messages(lTimingReports, oPort):
    lDetails = []
    for oTimingReport in lTimingReports:
        sErrorMessage = generate_error_message(oTimingReport, oPort)
        lDetails.append(sErrorMessage)
    return lDetails


def generate_error_message(oTimingReport, oPort):
    sMessage = f'capture clock period {oTimingReport.capture_clock.period:.3f}ns, configured period {oPort.capture_clock.period:.3f}ns'
    return rule_details.format_detail(oTimingReport.capture_clock_line, sMessage)
