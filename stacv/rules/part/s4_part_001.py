'''
:Stage: 4 - configuration
:Applies to: SDR-SS-O
:Reads: capture clock edge type in the ``requirement`` of every timing report, ``capture_edge`` of the part pin in the part
:Depends on: none

The part states whether each data pin captures on the rising or falling edge of its clock pin.
The capture clock edge in every timing report must be that edge type.
Every timing report is checked, setup and hold, at every process corner.
If the edge type differs, the timing report times the data against an edge the part does not capture on.

**Violation**

The part pin is configured with ``capture_edge = "Falling"``, but the timing report times the rising edge of ``dac_sclk``:

.. code-block:: text
   :emphasize-lines: 2

     Path Type:              Max at Fast Process Corner
     Requirement:            10.000ns  (dac_sclk rise@50.000ns - clk_100mhz rise@40.000ns)

**Result**

When the rule fails, it lists each timing report whose capture clock edge type differs, with the file and line of the requirement:

.. code-block:: text

     O_DAC_DATA_timing.rpt:82  capture clock edge rise, part SDIN captures on Falling

**Likely causes**

* The output delay constraint refers to the wrong edge of the capture clock.
* The capture edge of the pin in the part file is wrong.
* The configured capture edges are the wrong edge type, and the timing constraints were written to match them.

Refer to the vendor's timing constraints documentation for output delays.
'''

from stacv.results import rule_result
from stacv.rules import path_lookups
from stacv.rules import rule_details


RULE_ID = 's4_part_001'
FAILURE_MESSAGE = 'Capture clock edge type in timing reports does not match the capture edge of the part pin.'
TIMING_REPORT_EDGE_TYPES = {'Rising': 'rise', 'Falling': 'fall'}


def check(oPortProfile):
    '''
    Purpose:  Compares the capture clock edge type in the timing reports to the capture edge of the part pin.
    '''
    oPartPin = path_lookups.get_part_data_pin(oPortProfile)
    lMismatchedTimingReports = get_mismatched_timing_reports(oPortProfile.timing_reports.reports, oPartPin)
    lDetails = generate_error_messages(lMismatchedTimingReports, oPartPin)

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_mismatched_timing_reports(lTimingReports, oPartPin):
    lMismatchedTimingReports = []
    for oTimingReport in lTimingReports:
        if capture_clock_edge_type_differs(oTimingReport, oPartPin):
            lMismatchedTimingReports.append(oTimingReport)
    return lMismatchedTimingReports


def capture_clock_edge_type_differs(oTimingReport, oPartPin):
    return oTimingReport.capture_clock_edge_type != TIMING_REPORT_EDGE_TYPES[oPartPin.capture_edge]


def generate_error_messages(lTimingReports, oPartPin):
    lDetails = []
    for oTimingReport in lTimingReports:
        sErrorMessage = generate_error_message(oTimingReport, oPartPin)
        lDetails.append(sErrorMessage)
    return lDetails


def generate_error_message(oTimingReport, oPartPin):
    sMessage = f'capture clock edge {oTimingReport.capture_clock_edge_type}, part {oPartPin.name} captures on {oPartPin.capture_edge}'
    return rule_details.format_detail(oTimingReport.requirement_line, sMessage)
