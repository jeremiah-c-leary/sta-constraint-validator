'''
:Stage: 4 - configuration
:Applies to: all
:Reads: ``launch_clock`` period of every timing report, ``launch_clock.period`` of the port in the configuration
:Depends on: none

The period of the launch clock in every timing report must match the period configured for the port's launch clock.
Every timing report is checked, setup and hold, at every process corner.
The configured period is in nanoseconds.
The period matches when it is within 0.0005 ns of the configured period, half of the last digit printed in the timing report.
If the period differs, the timing constraints do not describe the clock the design runs on, and every timing result for the port is suspect.

**Violation**

The port is configured with ``launch_clock = {name = "clk_100mhz", period = 10}``, but the timing report gives 8.000 ns:

.. code-block:: text
   :emphasize-lines: 2

     Source:                 q_spi_data_reg/C
                               (rising edge-triggered cell FDCE clocked by clk_100mhz  {rise@0.000ns fall@4.000ns period=8.000ns})

**Result**

When the rule fails, it lists each timing report whose launch clock period differs, with the file and line of the launch clock:

.. code-block:: text

     O_DAC_DATA_timing.rpt:16  launch clock period 8.000ns, configured period 10.000ns

**Likely causes**

* The launch clock period in the configuration is wrong.
* The period of the clock in the timing constraints is wrong.

Refer to the vendor's timing constraints documentation for creating clocks.
'''

from stacv.rules import clock_comparisons
from stacv.rules import rule_details
from stacv.rules import tolerance


RULE_ID = 's4_launch_clock_002'
FAILURE_MESSAGE = 'Launch clock period in configuration does not match clock period in all timing reports.'
TOLERANCE = 0.0005


def check(oPortProfile):
    '''
    Purpose:  Compares the configuration launch clock period to the launch clock period in the timing reports.
    '''
    lDetails = get_launch_clock_mismatches(oPortProfile)

    return clock_comparisons.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_launch_clock_mismatches(oPortProfile):
    fConfigurationLaunchClockPeriod = oPortProfile.port.launch_clock.period
    lDetails = []
    for oTimingReport in oPortProfile.timing_reports.reports:
        fTimingReportLaunchClockPeriod = oTimingReport.launch_clock.period
        if not tolerance.is_within_tolerance(fConfigurationLaunchClockPeriod, fTimingReportLaunchClockPeriod, TOLERANCE):
            sErrorMessage = generate_error_message(oTimingReport, fConfigurationLaunchClockPeriod, fTimingReportLaunchClockPeriod)
            lDetails.append(sErrorMessage)
    return lDetails


def generate_error_message(oTimingReport, fConfigurationLaunchClockPeriod, fTimingReportLaunchClockPeriod):
    sMessage = f'launch clock period {fTimingReportLaunchClockPeriod:.3f}ns, configured period {fConfigurationLaunchClockPeriod:.3f}ns'
    return rule_details.format_detail(oTimingReport.launch_clock_line, sMessage)
