'''
:Stage: 4 - configuration
:Applies to: all
:Reads: ``launch_clock`` name of every timing report, ``launch_clock.name`` of the port in the configuration
:Depends on: none

The clock that launches the data in every timing report must be the launch clock configured for the port.
Every timing report is checked, setup and hold, at every process corner.
If the name differs, the timing report does not time the data from the clock the analysis is about, so its results do not apply to the interface.

**Violation**

The port is configured with ``launch_clock = {name = "clk_100mhz", period = 10}``, but the data is launched by ``clk_50mhz``:

.. code-block:: text
   :emphasize-lines: 2

     Source:                 q_spi_data_reg/C
                               (rising edge-triggered cell FDCE clocked by clk_50mhz  {rise@0.000ns fall@10.000ns period=20.000ns})

**Result**

When the rule fails, it lists each timing report whose launch clock differs, with the file and line of the launch clock:

.. code-block:: text

     O_DAC_DATA_timing.rpt:16  launch clock clk_50mhz, configured launch clock clk_100mhz

**Likely causes**

* The launch clock name in the configuration is wrong.
* The register driving the port is in a different clock domain than intended.
* The clock was renamed in the timing constraints, or the timing reports were generated from an older design.

Refer to the vendor's timing constraints documentation for creating clocks.
'''

from stacv.results import rule_result
from stacv.rules import clock_comparisons

RULE_ID = 's4_launch_clock_001'
FAILURE_MESSAGE = 'Launch clock name in configuration does not match clock name in all timing reports.'


def check(oPortProfile):
    '''
    Purpose:  Compares the configuration launch clock name to the launch clock name in the timing reports.
    '''
    lDetails = get_launch_clock_mismatches(oPortProfile)

    if has_mismatches(lDetails):
        return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetails, FAILURE_MESSAGE)
    return rule_result.RuleResult(RULE_ID, rule_result.PASSED, [], '')


def get_launch_clock_mismatches(oPortProfile):
    sConfigurationLaunchClockName = oPortProfile.port.launch_clock.name
    lDetails = []
    for oTimingReport in oPortProfile.timing_reports.reports:
        sTimingReportLaunchClockName = oTimingReport.launch_clock.name
        if sConfigurationLaunchClockName != sTimingReportLaunchClockName:
            sErrorMessage = generate_error_message(oTimingReport, sConfigurationLaunchClockName, sTimingReportLaunchClockName)
            lDetails.append(sErrorMessage)
    return lDetails


def generate_error_message(oTimingReport, sConfigurationLaunchClockName, sTimingReportLaunchClockName):
    sFilename = oTimingReport.launch_clock_line.filename
    iLineNumber = oTimingReport.launch_clock_line.line_number
    sMessage = f'launch clock {sTimingReportLaunchClockName}, configured launch clock {sConfigurationLaunchClockName}'
    return f'{sFilename}:{iLineNumber}  {sMessage}'


def has_mismatches(lDetails):
    return len(lDetails) > 0
