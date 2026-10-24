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
from stacv.rules import rule_details


RULE_ID = 's4_launch_clock_001'
FAILURE_MESSAGE = 'Launch clock name in configuration does not match clock name in all timing reports.'


def check(oPortProfile):
    '''
    Purpose:  Compares the configuration launch clock name to the launch clock name in the timing reports.
    '''
    lMismatchedTimingReports = get_mismatched_timing_reports(oPortProfile.timing_reports.reports, oPortProfile.port)
    lDetails = generate_error_messages(lMismatchedTimingReports, oPortProfile.port)

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_mismatched_timing_reports(lTimingReports, oPort):
    lMismatchedTimingReports = []
    for oTimingReport in lTimingReports:
        if launch_clock_name_differs(oTimingReport, oPort):
            lMismatchedTimingReports.append(oTimingReport)
    return lMismatchedTimingReports


def launch_clock_name_differs(oTimingReport, oPort):
    return oTimingReport.launch_clock.name != oPort.launch_clock.name


def generate_error_messages(lTimingReports, oPort):
    lDetails = []
    for oTimingReport in lTimingReports:
        sErrorMessage = generate_error_message(oTimingReport, oPort)
        lDetails.append(sErrorMessage)
    return lDetails


def generate_error_message(oTimingReport, oPort):
    sMessage = f'launch clock {oTimingReport.launch_clock.name}, configured launch clock {oPort.launch_clock.name}'
    return rule_details.format_detail(oTimingReport.launch_clock_line, sMessage)
