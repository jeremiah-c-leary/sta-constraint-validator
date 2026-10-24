'''
:Stage: 4 - configuration
:Applies to: all
:Reads: ``requirement`` of every setup timing report, ``launch_clock.period``, ``launch_clock.setup_edge``, ``capture_clock.period`` and ``capture_clock.setup_edge`` of the port in the configuration
:Depends on: none

The setup requirement in every setup timing report must match the time between the configured setup edges.
Every setup timing report is checked, at every process corner.
The time of an edge is (period / 2) * n, where n is the edge number for the launch clock, and the position of the edge letter for the capture clock, starting at 0 for A.
The expected setup requirement is the time of the capture setup edge minus the time of the launch setup edge.
Only the difference is compared, because the timing tool can time a later pair of edges with the same relationship.
The duty cycle of both clocks is assumed to be 50%, and phase offsets are not considered.
The requirement matches when it is within 0.0005 ns of the expected requirement, half of the last digit printed in the timing report.
If the requirement differs, the timing report does not time the edges the analysis is about, so its results do not apply to the interface.

**Violation**

The port is configured with ``launch_clock = {name = "clk_100mhz", period = 10.000, setup_edge = 8, hold_edge = 8}`` and ``capture_clock = {port = "O_DAC_SCLK", name = "dac_sclk", period = 50.000, setup_edge = "D", hold_edge = "B"}``.
Edge 8 is at 40.000 ns and edge D is at 75.000 ns, an expected setup requirement of 35.000 ns, but the timing report gives 10.000 ns:

.. code-block:: text
   :emphasize-lines: 2

     Path Type:              Max at Fast Process Corner
     Requirement:            10.000ns  (dac_sclk rise@50.000ns - clk_100mhz rise@40.000ns)

**Result**

When the rule fails, it lists each timing report whose setup requirement differs, with the file and line of the requirement:

.. code-block:: text

     O_DAC_DATA_timing.rpt:82  setup requirement 10.000ns, configured setup requirement 35.000ns

**Likely causes**

* The setup edges in the configuration are wrong.
* A multicycle path constraint for setup is missing, or has the wrong number of cycles.
* The output delay constraint refers to the wrong edge of the capture clock.

Refer to the vendor's timing constraints documentation for multicycle paths and output delays.
'''

from stacv.rules import clock_comparisons
from stacv.rules import edge_times
from stacv.rules import rule_details
from stacv.rules import tolerance


RULE_ID = 's4_requirement_001'
FAILURE_MESSAGE = 'Setup requirement in timing reports does not match the time between the configured setup edges.'
TOLERANCE = 0.0005


def check(oPortProfile):
    '''
    Purpose:  Compares the setup requirement in the setup timing reports to the time between the configured setup edges.
    '''
    lDetails = get_setup_requirement_mismatches(oPortProfile)

    return clock_comparisons.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_setup_requirement_mismatches(oPortProfile):
    fConfigurationRequirement = calculate_configuration_setup_requirement(oPortProfile.port)
    lDetails = []
    for oTimingReport in oPortProfile.timing_reports.get_setup_reports():
        if not tolerance.is_within_tolerance(fConfigurationRequirement, oTimingReport.requirement, TOLERANCE):
            sErrorMessage = generate_error_message(oTimingReport, fConfigurationRequirement)
            lDetails.append(sErrorMessage)
    return lDetails


def calculate_configuration_setup_requirement(oPort):
    iCaptureEdgeNumber = edge_times.convert_edge_letter_to_number(oPort.capture_clock.setup_edge)
    fCaptureEdgeTime = edge_times.calculate_edge_time(oPort.capture_clock.period, iCaptureEdgeNumber)
    fLaunchEdgeTime = edge_times.calculate_edge_time(oPort.launch_clock.period, oPort.launch_clock.setup_edge)
    return fCaptureEdgeTime - fLaunchEdgeTime


def generate_error_message(oTimingReport, fConfigurationRequirement):
    sMessage = f'setup requirement {oTimingReport.requirement:.3f}ns, configured setup requirement {fConfigurationRequirement:.3f}ns'
    return rule_details.format_detail(oTimingReport.requirement_line, sMessage)
