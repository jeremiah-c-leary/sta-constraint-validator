'''
:Stage: 0 - inputs
:Applies to: SDR-SS-I, SDR-SS-RT-DO, SDR-SYS-O, SDR-SYS-I, DDR-SS-I-SE, DDR-SS-I-NE
:Reads: first element of the capture clock path of an input, or of the launch clock path of an output, of every timing report, ``port`` of the forwarded clock in the configuration
:Depends on: none

A clock from the part, or from a clock source, enters the device on a port, and is created there.
The clock path inside the device must start at that port:
the capture clock path of an input, and the launch clock path of an output.
Every timing report is checked, setup and hold, at every process corner.
The first element of the clock path is the net from the clock port, which the timing tool names after the port.
If the clock path starts anywhere else, the delay or the clock of the timing report is measured from a different clock, and the timing report is wrong without any warning.

The other clock path is empty: the input or output delay is measured from the clock at the port, so the timing tool has no clock path to report on that side.

**Violation**

The port is configured with ``launch_clock = {name = "mii_rx_clk", ...}``, a clock with ``port = "I_MII_RX_CLK"``, but the capture clock path of the timing report starts at ``I_CLK``:

.. code-block:: text
   :emphasize-lines: 3

                            (clock mii_rx_clk rise edge)    40.000    40.000 r
       K18                                               0.000    40.000 r  I_CLK (IN)
                            net (fo=0)                   0.000    40.000    I_CLK

**Result**

When the rule fails, it lists each timing report whose clock path starts somewhere else, with the file and line of the first element of the clock path:

.. code-block:: text

     I_MII_RX_DV_timing.rpt:48  capture clock path starts at I_CLK, configured clock port I_MII_RX_CLK

**Likely causes**

* The clock port in the configuration is wrong.
* The clock was created on a different port, or the input or output delay refers to a clock created somewhere else.
* The wrong timing report is listed under the port.

Refer to the vendor's timing constraints documentation for clocks created on ports.
'''

from stacv.methodology import methodology
from stacv.results import rule_result
from stacv.rules import rule_details


RULE_ID = 's0_clock_path_003'
FAILURE_MESSAGE = 'Clock path in timing reports does not start at the configured clock port.'


def check(oPortProfile):
    '''
    Purpose:  Compares the first element of the clock path in the timing reports to the configured clock port.
    '''
    lDetails = get_clock_path_start_mismatches(oPortProfile)

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_clock_path_start_mismatches(oPortProfile):
    sClockPortName = oPortProfile.port.forwarded_clock.port
    sPathName = get_clock_path_name(oPortProfile.port)
    lDetails = []
    for oTimingReport in oPortProfile.timing_reports.reports:
        oClockPath = get_clock_path(oTimingReport, oPortProfile.port)
        if oClockPath.has_no_delays():
            lDetails.append(rule_details.format_detail(oClockPath.first_line, f'{sPathName} has no elements'))
            continue
        oClockPathStart = oClockPath.get_first_delay()
        if oClockPathStart.resource != sClockPortName:
            lDetails.append(generate_error_message(oClockPathStart, sPathName, sClockPortName))
    return lDetails


def get_clock_path(oTimingReport, oPort):
    # The delay of an input is measured from the launch clock at the port, so the device's clock path is the capture side.
    if oPort.data_direction == methodology.INPUT:
        return oTimingReport.capture_clock_path
    return oTimingReport.launch_clock_path


def get_clock_path_name(oPort):
    if oPort.data_direction == methodology.INPUT:
        return 'capture clock path'
    return 'launch clock path'


def generate_error_message(oClockPathStart, sPathName, sClockPortName):
    sMessage = f'{sPathName} starts at {oClockPathStart.resource}, configured clock port {sClockPortName}'
    return rule_details.format_detail(oClockPathStart.line, sMessage)
