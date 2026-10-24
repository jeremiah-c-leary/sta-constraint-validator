'''
:Stage: 4 - configuration
:Applies to: all
:Reads: ``capture_clock`` name of every timing report, ``capture_clock.name`` of the port in the configuration
:Depends on: none

The clock that captures the data in every timing report must be the capture clock configured for the port.
Every timing report is checked, setup and hold, at every process corner.
In a source synchronous output, the capture clock is the clock the output delay constraint refers to: the clock forwarded to the part.
If the name differs, the output delay is constrained against a different clock, and the timing report does not time the data against the clock the part uses.

**Violation**

The port is configured with ``capture_clock = {port = "O_DAC_SCLK", name = "dac_sclk", period = 20}``, but the data is captured by ``spi_sclk``:

.. code-block:: text
   :emphasize-lines: 2

     Destination:            O_DAC_DATA
                               (output port clocked by spi_sclk  {rise@0.000ns fall@25.000ns period=50.000ns})

**Result**

When the rule fails, it lists each timing report whose capture clock differs, with the file and line of the capture clock:

.. code-block:: text

     O_DAC_DATA_timing.rpt:18  capture clock spi_sclk, configured capture clock dac_sclk

**Likely causes**

* The capture clock name in the configuration is wrong.
* The output delay constraint refers to the wrong clock.
* The clock was renamed in the timing constraints, or the timing reports were generated from an older design.

Refer to the vendor's timing constraints documentation for output delays and generated clocks.
'''

from stacv.results import rule_result
from stacv.rules import rule_details


RULE_ID = 's4_capture_clock_001'
FAILURE_MESSAGE = 'Capture clock name in configuration does not match clock name in all timing reports.'


def check(oPortProfile):
    '''
    Purpose:  Compares the configuration capture clock name to the capture clock name in the timing reports.
    '''
    lMismatchedTimingReports = get_mismatched_timing_reports(oPortProfile.timing_reports.reports, oPortProfile.port)
    lDetails = generate_error_messages(lMismatchedTimingReports, oPortProfile.port)

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_mismatched_timing_reports(lTimingReports, oPort):
    lMismatchedTimingReports = []
    for oTimingReport in lTimingReports:
        if capture_clock_name_differs(oTimingReport, oPort):
            lMismatchedTimingReports.append(oTimingReport)
    return lMismatchedTimingReports


def capture_clock_name_differs(oTimingReport, oPort):
    return oTimingReport.capture_clock.name != oPort.capture_clock.name


def generate_error_messages(lTimingReports, oPort):
    lDetails = []
    for oTimingReport in lTimingReports:
        sErrorMessage = generate_error_message(oTimingReport, oPort)
        lDetails.append(sErrorMessage)
    return lDetails


def generate_error_message(oTimingReport, oPort):
    sMessage = f'capture clock {oTimingReport.capture_clock.name}, configured capture clock {oPort.capture_clock.name}'
    return rule_details.format_detail(oTimingReport.capture_clock_line, sMessage)
