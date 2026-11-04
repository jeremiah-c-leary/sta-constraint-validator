'''
:Stage: 4 - configuration
:Applies to: DDR-SS-I-SE, DDR-SS-I-NE
:Reads: launch and capture clock edge types in the ``requirement`` of every timing report
:Depends on: none

A double data rate input captures each bit on the edge its methodology names, so every timing report must pair the edges that edge gives:

===========  ===================================  ===================================
Methodology  Setup timing report                  Hold timing report
===========  ===================================  ===================================
DDR-SS-I-SE  same edge type: rise to rise,        other edge type: rise to fall,
             fall to fall                         fall to rise
DDR-SS-I-NE  other edge type: rise to fall,       same edge type: rise to rise,
             fall to rise                         fall to fall
===========  ===================================  ===================================

The timing tool times every pair of edges unless the constraints remove the ones that do not capture the data.
A pair that does not capture the data usually meets timing, so a missing false path shows only as a report that times the wrong edges.
s4_requirement_001 and s4_requirement_002 can still pass, since the wrong pair can give the same requirement.

**Violation**

A DDR-SS-I-SE port, whose setup check is from an edge to the same edge type, has a setup timing report from a falling edge to a rising edge:

.. code-block:: text

     Requirement:            20.000ns  (rgmii_rxc rise@40.000ns - rgmii_rxc fall@20.000ns)

**Result**

When the rule fails, it lists each timing report that pairs the wrong edge types, with the file and line of its requirement:

.. code-block:: text

     I_RGMII_RX_CTL_timing.rpt:21  setup timing report times fall to rise; a DDR-SS-I-SE port captures each bit on the edge it is aligned with, so its setup timing reports time the same edge type

**Likely causes**

* The false paths of the edge pairs that do not capture the data are missing, or do not run through the data port.
* The methodology does not match the edge the design captures on.

Refer to the vendor's timing constraints documentation for double data rate interfaces.
'''

from stacv.results import rule_result
from stacv.rules import rule_details


RULE_ID = 's4_edge_002'
FAILURE_MESSAGE = 'Timing reports pair launch and capture edges the methodology does not capture on.'
SAME_EDGE_TYPE = 'the same edge type'
OTHER_EDGE_TYPE = 'the other edge type'


def check(oPortProfile):
    '''
    Purpose:  Checks the launch and capture edge types of every timing report pair as the methodology captures.
    '''
    oPort = oPortProfile.port
    lDetails = []
    lDetails.extend(find_wrong_edge_pairs(oPort, oPortProfile.timing_reports.get_setup_reports(), 'setup', setup_is_same_edge_type(oPort)))
    lDetails.extend(find_wrong_edge_pairs(oPort, oPortProfile.timing_reports.get_hold_reports(), 'hold', not setup_is_same_edge_type(oPort)))

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def setup_is_same_edge_type(oPort):
    # An even number of edges after the launch edge is an edge of the same type.
    return oPort.setup_capture_edges_after_launch % 2 == 0


def find_wrong_edge_pairs(oPort, lTimingReports, sCheck, bSameEdgeType):
    lDetails = []
    for oTimingReport in lTimingReports:
        if pairs_same_edge_type(oTimingReport) != bSameEdgeType:
            lDetails.append(generate_error_message(oPort, oTimingReport, sCheck, bSameEdgeType))
    return lDetails


def pairs_same_edge_type(oTimingReport):
    return oTimingReport.launch_clock_edge_type == oTimingReport.capture_clock_edge_type


def generate_error_message(oPort, oTimingReport, sCheck, bSameEdgeType):
    sPair = f'{oTimingReport.launch_clock_edge_type} to {oTimingReport.capture_clock_edge_type}'
    sExpected = describe_edge_type(bSameEdgeType)
    sMessage = f'{sCheck} timing report times {sPair}; {oPort.capture_edge_description}, so its {sCheck} timing reports time {sExpected}'
    return rule_details.format_detail(oTimingReport.requirement_line, sMessage)


def describe_edge_type(bSameEdgeType):
    if bSameEdgeType:
        return SAME_EDGE_TYPE
    return OTHER_EDGE_TYPE
