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

The port is configured with ``capture_clock = {port = "O_DAC_SCLK", name = "dac_sclk", frequency = 20}``, but the data is captured by ``spi_sclk``:

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

RULE_ID = 's4_capture_clock_001'
FAILURE_MESSAGE = 'Capture clock name in configuration does not match clock name over all timing reports.'


def check(oPortProfile):
    '''
    Purpose:  Compares the configuration capture clock name to the capture clock name in the timing reports.
    '''
    lDetails = get_capture_clock_mismatches(oPortProfile)

    if not capture_clock_names_matched(lDetails):
        return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetails, FAILURE_MESSAGE)
    return rule_result.RuleResult(RULE_ID, rule_result.PASSED, [], '')


def get_capture_clock_mismatches(oPortProfile):
    sConfigurationCaptureClockName = oPortProfile.port.capture_clock.name
    lDetails = []
    for oTimingReport in oPortProfile.timing_reports.reports:
        sTimingReportCaptureClockName = oTimingReport.capture_clock.name
        if sConfigurationCaptureClockName != sTimingReportCaptureClockName:
            sErrorMessage = generate_error_message(oTimingReport, sConfigurationCaptureClockName, sTimingReportCaptureClockName)
            lDetails.append(sErrorMessage)
    return lDetails


def generate_error_message(oTimingReport, sConfigurationCaptureClockName, sTimingReportCaptureClockName):
    sFilename = oTimingReport.capture_clock_line.filename
    iLineNumber = oTimingReport.capture_clock_line.line_number
    sMessage = f'capture clock {sTimingReportCaptureClockName}, configured capture clock {sConfigurationCaptureClockName}"'
    return f'{sFilename}:{iLineNumber}  {sMessage}'


def capture_clock_names_matched(lDetails):
    return len(lDetails) == 0
