'''
:Stage: 4 - configuration
:Applies to: DDR-SS-O, DDR-SS-I-SE, DDR-SS-I-NE
:Reads: forwarded clock edge type in the ``requirement`` of every timing report
:Depends on: none

Double data rate data changes on both edges of the clock that crosses the board, so both edges must be timed.
The setup timing reports must include at least one report timed from each edge type of that clock, rising and falling, and so must the hold timing reports.
The clock is the capture clock of an output, which the device forwards, and the launch clock of an input, which the part sends.

The delays of the falling edges are applied with ``-clock_fall -add_delay``.
Without ``-clock_fall``, the timing tool assumes the data changes only on the rising edges; without ``-add_delay``, the falling edge delay replaces the rising edge delay.
Either way, half of the data is not timed, and the timing reports of the other half still meet timing.

**Violation**

Every setup timing report times the rising edge of ``rgmii_rxc``:

.. code-block:: text

     Requirement:            0.000ns  (rgmii_rxc rise@0.000ns - rgmii_rxc rise@0.000ns)

**Result**

When the rule fails, it gives the file and line of the requirement of the first timing report of the setup or hold reports missing an edge type:

.. code-block:: text

     I_RGMII_RX_CTL_timing.rpt:21  setup timing reports time only the rise edges of rgmii_rxc

**Likely causes**

* The ``-clock_fall`` input or output delay is missing, or was applied without ``-add_delay``.
* The timing report was generated with too few paths to include both edges.

Refer to the vendor's timing constraints documentation for double data rate interfaces.
'''

from stacv.methodology import methodology
from stacv.results import rule_result
from stacv.rules import rule_details


RULE_ID = 's4_edge_001'
FAILURE_MESSAGE = 'Timing reports do not time both edges of the double data rate clock.'
EDGE_TYPES = ['rise', 'fall']


def check(oPortProfile):
    '''
    Purpose:  Checks the setup and the hold timing reports each time both edge types of the forwarded clock.
    '''
    lDetails = []
    lDetails.extend(find_missing_edge_types(oPortProfile, oPortProfile.timing_reports.get_setup_reports(), 'setup'))
    lDetails.extend(find_missing_edge_types(oPortProfile, oPortProfile.timing_reports.get_hold_reports(), 'hold'))

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def find_missing_edge_types(oPortProfile, lTimingReports, sCheck):
    if len(lTimingReports) == 0:
        return []
    lEdgeTypes = collect_edge_types(oPortProfile.port, lTimingReports)
    if has_both_edge_types(lEdgeTypes):
        return []
    sMessage = f'{sCheck} timing reports time only the {" and ".join(lEdgeTypes)} edges of {oPortProfile.port.forwarded_clock.name}'
    return [rule_details.format_detail(lTimingReports[0].requirement_line, sMessage)]


def collect_edge_types(oPort, lTimingReports):
    lEdgeTypes = []
    for oTimingReport in lTimingReports:
        sEdgeType = get_forwarded_clock_edge_type(oPort, oTimingReport)
        if sEdgeType not in lEdgeTypes:
            lEdgeTypes.append(sEdgeType)
    return lEdgeTypes


def get_forwarded_clock_edge_type(oPort, oTimingReport):
    if oPort.forwarded_clock_key == methodology.LAUNCH_CLOCK:
        return oTimingReport.launch_clock_edge_type
    return oTimingReport.capture_clock_edge_type


def has_both_edge_types(lEdgeTypes):
    for sEdgeType in EDGE_TYPES:
        if sEdgeType not in lEdgeTypes:
            return False
    return True
