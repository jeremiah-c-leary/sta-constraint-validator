'''
:Stage: 0 - inputs
:Applies to: SDR-SS-RT
:Reads: last element of the launch clock path of every timing report, ``launch_clock.port`` of the port in the configuration
:Depends on: none

The launch clock path of every timing report of a port must end at the configured clock port.
Every timing report is checked, setup and hold, at every process corner.
In a round trip, the device forwards the launch clock to the part, so the launch clock path runs through the device to the clock port, where the input delay starts.
The last element of the launch clock path is the net to the clock port, which the timing tool names after the port.
If the launch clock path ends anywhere else, the delay of the forwarded clock through the device is left out, and the timing report is wrong without any warning.

**Violation**

The port is configured with ``launch_clock = {port = "O_DAC_CSF", ...}``, but the launch clock path of the timing report ends at ``O_DAC_SCLK``:

.. code-block:: text
   :emphasize-lines: 2

       W17                  OBUF (Prop_obuf_I_O)         2.344     8.200 r  O_DAC_SCLK_OBUF_inst/O
                            net (fo=0)                   0.000     8.200    O_DAC_SCLK

**Result**

When the rule fails, it lists each timing report whose launch clock path ends somewhere else, with the file and line of the last element of the launch clock path:

.. code-block:: text

     I_DAC_DATA_timing.rpt:48  launch clock path ends at O_DAC_SCLK, configured clock port O_DAC_CSF

**Likely causes**

* The clock port in the configuration is wrong.
* The input delay constraint has no ``-reference_pin``, so the launch clock path ends where the clock is generated.
* The input delay constraint refers to a clock that is not forwarded on the clock port.
* The wrong timing report is listed under the port.
'''

from stacv.results import rule_result
from stacv.rules import rule_details


RULE_ID = 's0_clock_path_002'
FAILURE_MESSAGE = 'Launch clock path in timing reports does not end at the configured clock port.'


def check(oPortProfile):
    '''
    Purpose:  Compares the last element of the launch clock path in the timing reports to the configured clock port.
    '''
    lDetails = get_launch_clock_path_end_mismatches(oPortProfile)

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_launch_clock_path_end_mismatches(oPortProfile):
    sClockPortName = oPortProfile.port.launch_clock.port
    lDetails = []
    for oTimingReport in oPortProfile.timing_reports.reports:
        oLaunchClockPathEnd = oTimingReport.launch_clock_path.get_last_delay()
        if oLaunchClockPathEnd.resource != sClockPortName:
            sErrorMessage = generate_error_message(oLaunchClockPathEnd, sClockPortName)
            lDetails.append(sErrorMessage)
    return lDetails


def generate_error_message(oLaunchClockPathEnd, sClockPortName):
    sMessage = f'launch clock path ends at {oLaunchClockPathEnd.resource}, configured clock port {sClockPortName}'
    return rule_details.format_detail(oLaunchClockPathEnd.line, sMessage)
