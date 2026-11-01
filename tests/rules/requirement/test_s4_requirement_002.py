import os

from tests.rules import rule_test_case

sTestDir = os.path.dirname(os.path.abspath(__file__))
sParseDir = os.path.join(sTestDir, '..', '..', 'timing_report', 'parse', 'vivado')

# Every hold timing report in this file has a requirement of 0.000ns, on lines 21 and 165.
# Every setup timing report has a requirement of 10.000ns, on lines 82 and 226.
sTimingReport = os.path.abspath(os.path.join(sParseDir, 'O_DAC_DATA_timing.rpt'))
lHoldRequirementLines = [21, 165]
lSetupRequirementLines = [82, 226]

sRuleId = 's4_requirement_002'

# With a launch clock period of 10.000ns and a capture clock period of 50.000ns:
#    launch edge 0   is at (10.000 / 2) * 0 = 0.000ns
#    capture edge A  is at (50.000 / 2) * 0 = 0.000ns
# which gives a hold requirement of 0.000 - 0.000 = 0.000ns.
iPassingLaunchHoldEdge = 0
sPassingCaptureHoldEdge = 'A'
fPassingCapturePeriod = 50.0

# Edge A is at 0.000ns for any period, so the rounding tests use a later pair of edges:
#    launch edge 10  is at (10.000 / 2) * 10 = 50.000ns
#    capture edge C  is at (50.000 / 2) * 2  = 50.000ns
iRoundingLaunchHoldEdge = 10
sRoundingCaptureHoldEdge = 'C'


def build_config_text(sPartFile, sTracesFile, sTimingReportFile, oHoldEdges):
    lText = []
    lText.append('description = "s4_requirement_002 test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[clock]]')
    lText.append('name = "clk_100mhz"')
    lText.append('period = 10.000')
    lText.append('[[clock]]')
    lText.append('name = "dac_sclk"')
    lText.append(f'period = {oHoldEdges.capture_period}')
    lText.append('port = "O_DAC_SCLK"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append(f'launch_clock = {{name = "clk_100mhz", setup_edge = 8, hold_edge = {oHoldEdges.launch_edge}}}')
    lText.append(f'capture_clock = {{name = "dac_sclk", setup_edge = "C", hold_edge = "{oHoldEdges.capture_edge}"}}')
    lText.append(f'timing_reports = ["{sTimingReportFile}"]')
    return '\n'.join(lText)


class HoldEdges():

    def __init__(self, iLaunchEdge, sCaptureEdge, fCapturePeriod):
        self.launch_edge = iLaunchEdge
        self.capture_edge = sCaptureEdge
        self.capture_period = fCapturePeriod


class Test(rule_test_case.RuleTestCase):

    def execute_with_hold_edges(self, iLaunchEdge, sCaptureEdge):
        oHoldEdges = HoldEdges(iLaunchEdge, sCaptureEdge, fPassingCapturePeriod)
        return self.execute(oHoldEdges, sTimingReport)

    def execute_with_capture_period(self, fCapturePeriod):
        oHoldEdges = HoldEdges(iRoundingLaunchHoldEdge, sRoundingCaptureHoldEdge, fCapturePeriod)
        return self.execute(oHoldEdges, sTimingReport)

    def execute_with_requirement_lines_changed(self, lLineNumbers, sOld, sNew):
        return self.execute_with_hold_edges_and_requirement_lines_changed(iPassingLaunchHoldEdge, sPassingCaptureHoldEdge, lLineNumbers, sOld, sNew)

    def execute_with_hold_edges_and_requirement_lines_changed(self, iLaunchEdge, sCaptureEdge, lLineNumbers, sOld, sNew):
        lLines = rule_test_case.read_lines(sTimingReport)
        for iLineNumber in lLineNumbers:
            self.assertIn(sOld, lLines[iLineNumber - 1])
            lLines[iLineNumber - 1] = lLines[iLineNumber - 1].replace(sOld, sNew)
        rule_test_case.write_file(self.sChangedTimingReport, '\n'.join(lLines))
        oHoldEdges = HoldEdges(iLaunchEdge, sCaptureEdge, fPassingCapturePeriod)
        return self.execute(oHoldEdges, self.sChangedTimingReport)

    def execute(self, oHoldEdges, sTimingReportFile):
        rule_test_case.write_file(self.sInterfaceFile, build_config_text(self.sPartFile, self.sTracesFile, sTimingReportFile, oHoldEdges))
        rule_test_case.write_file(self.sPartFile, rule_test_case.build_passing_part_text())
        rule_test_case.write_file(self.sTracesFile, rule_test_case.build_passing_traces_text())
        return self.run_check()

    def test_passes_when_hold_requirement_matches_configured_hold_edges(self):
        self.execute_with_hold_edges(iPassingLaunchHoldEdge, sPassingCaptureHoldEdge)

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_hold_requirement_matches(self):
        iExitCode = self.execute_with_hold_edges(iPassingLaunchHoldEdge, sPassingCaptureHoldEdge)

        self.assertEqual(0, iExitCode)

    def test_fails_when_launch_hold_edge_differs(self):
        # (50.000 / 2) * 0 - (10.000 / 2) * 2 = 0.000 - 10.000 = -10.000
        self.execute_with_hold_edges(2, sPassingCaptureHoldEdge)

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_hold_requirement_differs(self):
        iExitCode = self.execute_with_hold_edges(2, sPassingCaptureHoldEdge)

        self.assertEqual(1, iExitCode)

    def test_fails_when_capture_hold_edge_differs(self):
        # (50.000 / 2) * 2 - (10.000 / 2) * 0 = 50.000 - 0.000 = 50.000
        self.execute_with_hold_edges(iPassingLaunchHoldEdge, 'C')

        self.assert_rule_failed(sRuleId)

    def test_fails_when_configured_hold_requirement_is_negative(self):
        # (50.000 / 2) * 0 - (10.000 / 2) * 8 = 0.000 - 40.000 = -40.000
        self.execute_with_hold_edges(8, 'A')

        self.assert_rule_failed(sRuleId)

    def test_passes_when_negative_hold_requirement_matches_configured_hold_edges(self):
        # (50.000 / 2) * 0 - (10.000 / 2) * 8 = 0.000 - 40.000 = -40.000
        self.execute_with_hold_edges_and_requirement_lines_changed(8, 'A', lHoldRequirementLines, 'Requirement:            0.000ns', 'Requirement:            -40.000ns')

        self.assert_rule_passed(sRuleId)

    def test_passes_when_a_later_pair_of_edges_has_the_same_hold_requirement(self):
        # (50.000 / 2) * 2 - (10.000 / 2) * 10 = 50.000 - 50.000 = 0.000
        self.execute_with_hold_edges(10, 'C')

        self.assert_rule_passed(sRuleId)

    def test_passes_when_configured_hold_requirement_is_above_by_less_than_rounding(self):
        # (50.0004 / 2) * 2 - 50.000 = 0.0004
        self.execute_with_capture_period(50.0004)

        self.assert_rule_passed(sRuleId)

    def test_passes_when_configured_hold_requirement_is_below_by_less_than_rounding(self):
        # (49.9996 / 2) * 2 - 50.000 = -0.0004
        self.execute_with_capture_period(49.9996)

        self.assert_rule_passed(sRuleId)

    def test_fails_when_configured_hold_requirement_is_above_by_more_than_rounding(self):
        # (50.0006 / 2) * 2 - 50.000 = 0.0006
        self.execute_with_capture_period(50.0006)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_configured_hold_requirement_is_below_by_more_than_rounding(self):
        # (49.9994 / 2) * 2 - 50.000 = -0.0006
        self.execute_with_capture_period(49.9994)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_one_hold_timing_report_has_a_different_requirement(self):
        self.execute_with_requirement_lines_changed([165], 'Requirement:            0.000ns', 'Requirement:            5.000ns')

        self.assert_rule_failed(sRuleId)

    def test_ignores_requirement_of_setup_timing_reports(self):
        self.execute_with_requirement_lines_changed(lSetupRequirementLines, 'Requirement:            10.000ns', 'Requirement:            20.000ns')

        self.assert_rule_passed(sRuleId)

    def test_failure_lists_each_hold_timing_report_with_a_different_requirement(self):
        self.execute_with_hold_edges(8, 'A')

        lExpected = []
        for iLineNumber in lHoldRequirementLines:
            lExpected.append(f'{sTimingReport}:{iLineNumber}  hold requirement 0.000ns, configured hold requirement -40.000ns')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)

    def test_failure_lists_only_the_hold_timing_report_with_a_different_requirement(self):
        self.execute_with_requirement_lines_changed([165], 'Requirement:            0.000ns', 'Requirement:            5.000ns')

        lExpected = []
        lExpected.append(f'{self.sChangedTimingReport}:165  hold requirement 5.000ns, configured hold requirement 0.000ns')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)
