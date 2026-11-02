'''
:Stage: 4 - configuration
:Applies to: SDR-SS-RT-DI
:Reads: launch clock edge type in the ``requirement`` of every timing report, ``launch_edge`` of the part pin in the part
:Depends on: none

The part states whether each data pin it drives launches on the rising or falling edge of its clock pin.
In a round trip, that clock is the launch clock the device forwards to the part, so the launch clock edge in every timing report must be that edge type.
Every timing report is checked, setup and hold, at every process corner.
If the edge type differs, the timing report times data the part launches on an edge it does not launch on.

**Violation**

The part pin is configured with ``launch_edge = "Falling"``, but the timing report times the rising edge of ``dac_sclk_rd``:

.. code-block:: text
   :emphasize-lines: 2

     Path Type:              Setup (Max at Slow Process Corner)
     Requirement:            40.000ns  (clk_100mhz rise@40.000ns - dac_sclk_rd rise@0.000ns)

**Result**

When the rule fails, it lists each timing report whose launch clock edge type differs, with the file and line of the requirement:

.. code-block:: text

     I_DAC_DATA_timing.rpt:21  launch clock edge rise, part SDO launches on Falling

**Likely causes**

* The input delay constraint refers to the wrong edge of the launch clock.
* The launch edge of the pin in the part file is wrong.
* The configured launch edges are the wrong edge type, and the timing constraints were written to match them.

Refer to the vendor's timing constraints documentation for input delays.
'''

from stacv.results import rule_result
from stacv.rules import path_lookups
from stacv.rules import rule_details


RULE_ID = 's4_part_002'
FAILURE_MESSAGE = 'Launch clock edge type in timing reports does not match the launch edge of the part pin.'
TIMING_REPORT_EDGE_TYPES = {'Rising': 'rise', 'Falling': 'fall'}


def check(oPortProfile):
    '''
    Purpose:  Compares the launch clock edge type in the timing reports to the launch edge of the part pin.
    '''
    lDetails = get_launch_clock_edge_type_mismatches(oPortProfile)

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_launch_clock_edge_type_mismatches(oPortProfile):
    oPartPin = path_lookups.get_part_data_pin(oPortProfile)
    sPartEdgeType = TIMING_REPORT_EDGE_TYPES[oPartPin.launch_edge]
    lDetails = []
    for oTimingReport in oPortProfile.timing_reports.reports:
        if oTimingReport.launch_clock_edge_type != sPartEdgeType:
            sErrorMessage = generate_error_message(oTimingReport, oPartPin)
            lDetails.append(sErrorMessage)
    return lDetails


def generate_error_message(oTimingReport, oPartPin):
    sMessage = f'launch clock edge {oTimingReport.launch_clock_edge_type}, part {oPartPin.name} launches on {oPartPin.launch_edge}'
    return rule_details.format_detail(oTimingReport.requirement_line, sMessage)
