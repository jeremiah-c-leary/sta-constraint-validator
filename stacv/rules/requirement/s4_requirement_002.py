'''
:Stage: 4 - configuration
:Applies to: all
:Reads: ``requirement`` of every hold timing report, ``launch_clock.period``, ``launch_clock.hold_edge``, ``capture_clock.period`` and ``capture_clock.hold_edge`` of the port in the configuration
:Depends on: none

The hold requirement in every hold timing report must match the time between the configured hold edges.
Every hold timing report is checked, at every process corner.
The time of an edge is (period / 2) * n, where n is the edge number for the launch clock, and the position of the edge letter for the capture clock, starting at 0 for A.
The expected hold requirement is the time of the capture hold edge minus the time of the launch hold edge.
It is negative when the capture hold edge comes before the launch hold edge, which is common for an interface clocked by a divided down clock.
Only the difference is compared, because the timing tool can time a later pair of edges with the same relationship.
The duty cycle of both clocks is assumed to be 50%, and phase offsets are not considered.
The requirement matches when it is within 0.0005 ns of the expected requirement, half of the last digit printed in the timing report.
If the requirement differs, the timing report does not time the edges the analysis is about, so its results do not apply to the interface.

**Violation**

The port is configured with ``launch_clock = {name = "clk_100mhz", period = 10.000, setup_edge = 8, hold_edge = 8}`` and ``capture_clock = {port = "O_DAC_SCLK", name = "dac_sclk", period = 50.000, setup_edge = "D", hold_edge = "B"}``.
Edge 8 is at 40.000 ns and edge B is at 25.000 ns, an expected hold requirement of -15.000 ns, but the timing report gives 0.000 ns:

.. code-block:: text
   :emphasize-lines: 2

     Path Type:              Min at Fast Process Corner
     Requirement:            0.000ns  (dac_sclk rise@0.000ns - clk_100mhz rise@0.000ns)

**Result**

When the rule fails, it lists each timing report whose hold requirement differs, with the file and line of the requirement:

.. code-block:: text

     O_DAC_DATA_timing.rpt:21  hold requirement 0.000ns, configured hold requirement -15.000ns

**Likely causes**

* The hold edges in the configuration are wrong.
* A multicycle path constraint for hold is missing, or has the wrong number of cycles.
  When a multicycle path moves the setup edges, the timing tool moves the hold edges with them unless told otherwise.
* The output delay constraint refers to the wrong edge of the capture clock.

Refer to the vendor's timing constraints documentation for multicycle paths and output delays.
'''

from stacv.results import rule_result
from stacv.rules import requirements
from stacv.rules import rule_details
from stacv.rules import tolerance


RULE_ID = 's4_requirement_002'
FAILURE_MESSAGE = 'Hold requirement in timing reports does not match the time between the configured hold edges.'
TOLERANCE = 0.0005


def check(oPortProfile):
    '''
    Purpose:  Compares the hold requirement in the hold timing reports to the time between the configured hold edges.
    '''
    lDetails = get_hold_requirement_mismatches(oPortProfile)

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_hold_requirement_mismatches(oPortProfile):
    fConfigurationRequirement = requirements.calculate_configuration_hold_requirement(oPortProfile.port)
    lDetails = []
    for oTimingReport in oPortProfile.timing_reports.get_hold_reports():
        if not tolerance.is_within_tolerance(fConfigurationRequirement, oTimingReport.requirement, TOLERANCE):
            sErrorMessage = generate_error_message(oTimingReport, fConfigurationRequirement)
            lDetails.append(sErrorMessage)
    return lDetails


def generate_error_message(oTimingReport, fConfigurationRequirement):
    sMessage = f'hold requirement {oTimingReport.requirement:.3f}ns, configured hold requirement {fConfigurationRequirement:.3f}ns'
    return rule_details.format_detail(oTimingReport.requirement_line, sMessage)
