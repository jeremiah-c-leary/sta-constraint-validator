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

from stacv.rules import clock_comparisons


RULE_ID = 's4_capture_clock_002'
FAILURE_MESSAGE = 'Capture clock period in configuration does not match clock period in all timing reports.'
TOLERANCE = 0.0005


def check(oPortProfile):
    '''
    Purpose:  Compares the configuration capture clock period to the capture clock period in the timing reports.
    '''
    lDetails = get_capture_clock_mismatches(oPortProfile)

    return clock_comparisons.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_capture_clock_mismatches(oPortProfile):
    fConfigurationCaptureClockPeriod = oPortProfile.port.capture_clock.period
    lDetails = []
    for oTimingReport in oPortProfile.timing_reports.reports:
        fTimingReportCaptureClockPeriod = oTimingReport.capture_clock.period
        if not clock_comparisons.clock_period_is_within_tolerance(fConfigurationCaptureClockPeriod, fTimingReportCaptureClockPeriod, TOLERANCE):
            sErrorMessage = generate_error_message(oTimingReport, fConfigurationCaptureClockPeriod, fTimingReportCaptureClockPeriod)
            lDetails.append(sErrorMessage)
    return lDetails


def generate_error_message(oTimingReport, fConfigurationCaptureClockPeriod, fTimingReportCaptureClockPeriod):
    sFilename = oTimingReport.capture_clock_line.filename
    iLineNumber = oTimingReport.capture_clock_line.line_number
    sMessage = f'capture clock period {fTimingReportCaptureClockPeriod:.3f}ns, configured period {fConfigurationCaptureClockPeriod:.3f}ns'
    return f'{sFilename}:{iLineNumber}  {sMessage}'
