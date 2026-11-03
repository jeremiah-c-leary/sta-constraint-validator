from tests.rules import rule_test_case

# Every setup timing report in this file has a requirement of 20.000ns, on lines 21 and 175.
# Every hold timing report has a requirement of -20.000ns, on lines 98 and 252.
sTimingReport = rule_test_case.sTimingReport
lSetupRequirementLines = rule_test_case.build_setup_lines(rule_test_case.iRequirementLine)
lHoldRequirementLines = rule_test_case.build_hold_lines(rule_test_case.iRequirementLine)
iSlowSetupRequirementLine = lSetupRequirementLines[0]

sRuleId = 's4_requirement_001'

# An SDR-SS-O port launches on one edge, and its capture hold edge is the capture edge before its setup edge.
# With a launch clock period of 10.000ns and a capture clock period of 40.000ns:
#    launch edge 8   is at (10.000 / 2) * 8 = 40.000ns
#    capture edge D  is at (40.000 / 2) * 3 = 60.000ns
# which gives a setup requirement of 60.000 - 40.000 = 20.000ns.
iPassingLaunchEdge = 8
sPassingCaptureSetupEdge = 'D'
sPassingCaptureHoldEdge = 'B'
fPassingCapturePeriod = 40.0


def build_config_text(sPartFile, sTracesFile, sTimingReportFile, oEdges):
    lText = []
    lText.append('description = "s4_requirement_001 test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append('part_interface = "Serial Interface"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[clock]]')
    lText.append('name = "clk_100mhz"')
    lText.append('period = 10.000')
    lText.append('[[clock]]')
    lText.append('name = "dac_sclk"')
    lText.append(f'period = {oEdges.capture_period}')
    lText.append('port = "O_DAC_SCLK"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append(f'launch_clock = {{name = "clk_100mhz", setup_edge = {oEdges.launch_edge}, hold_edge = {oEdges.launch_edge}}}')
    lText.append(f'capture_clock = {{name = "dac_sclk", setup_edge = "{oEdges.capture_setup_edge}", hold_edge = "{oEdges.capture_hold_edge}"}}')
    lText.append(f'timing_reports = ["{sTimingReportFile}"]')
    return '\n'.join(lText)


class Edges():

    def __init__(self, iLaunchEdge, sCaptureSetupEdge, sCaptureHoldEdge, fCapturePeriod):
        self.launch_edge = iLaunchEdge
        self.capture_setup_edge = sCaptureSetupEdge
        self.capture_hold_edge = sCaptureHoldEdge
        self.capture_period = fCapturePeriod


class Test(rule_test_case.RuleTestCase):

    def execute_with_edges(self, iLaunchEdge, sCaptureSetupEdge, sCaptureHoldEdge):
        oEdges = Edges(iLaunchEdge, sCaptureSetupEdge, sCaptureHoldEdge, fPassingCapturePeriod)
        return self.execute(oEdges, sTimingReport)

    def execute_with_capture_period(self, fCapturePeriod):
        oEdges = Edges(iPassingLaunchEdge, sPassingCaptureSetupEdge, sPassingCaptureHoldEdge, fCapturePeriod)
        return self.execute(oEdges, sTimingReport)

    def execute_with_requirement_lines_changed(self, lLineNumbers, sOld, sNew):
        lLines = rule_test_case.read_lines(sTimingReport)
        for iLineNumber in lLineNumbers:
            self.assertIn(sOld, lLines[iLineNumber - 1])
            lLines[iLineNumber - 1] = lLines[iLineNumber - 1].replace(sOld, sNew)
        rule_test_case.write_file(self.sChangedTimingReport, '\n'.join(lLines))
        oEdges = Edges(iPassingLaunchEdge, sPassingCaptureSetupEdge, sPassingCaptureHoldEdge, fPassingCapturePeriod)
        return self.execute(oEdges, self.sChangedTimingReport)

    def execute(self, oEdges, sTimingReportFile):
        rule_test_case.write_file(self.sInterfaceFile, build_config_text(self.sPartFile, self.sTracesFile, sTimingReportFile, oEdges))
        rule_test_case.write_file(self.sPartFile, rule_test_case.build_passing_part_text())
        rule_test_case.write_file(self.sTracesFile, rule_test_case.build_passing_traces_text())
        return self.run_check()

    def test_passes_when_setup_requirement_matches_configured_setup_edges(self):
        self.execute_with_edges(iPassingLaunchEdge, sPassingCaptureSetupEdge, sPassingCaptureHoldEdge)

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_setup_requirement_matches(self):
        iExitCode = self.execute_with_edges(iPassingLaunchEdge, sPassingCaptureSetupEdge, sPassingCaptureHoldEdge)

        self.assertEqual(0, iExitCode)

    def test_fails_when_launch_edge_differs(self):
        # (40.000 / 2) * 3 - (10.000 / 2) * 6 = 60.000 - 30.000 = 30.000
        self.execute_with_edges(6, sPassingCaptureSetupEdge, sPassingCaptureHoldEdge)

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_setup_requirement_differs(self):
        iExitCode = self.execute_with_edges(6, sPassingCaptureSetupEdge, sPassingCaptureHoldEdge)

        self.assertEqual(1, iExitCode)

    def test_fails_when_capture_setup_edge_differs(self):
        # (40.000 / 2) * 5 - (10.000 / 2) * 8 = 100.000 - 40.000 = 60.000
        self.execute_with_edges(iPassingLaunchEdge, 'F', 'D')

        self.assert_rule_failed(sRuleId)

    def test_passes_when_a_later_pair_of_edges_has_the_same_setup_requirement(self):
        # (40.000 / 2) * 5 - (10.000 / 2) * 16 = 100.000 - 80.000 = 20.000
        self.execute_with_edges(16, 'F', 'D')

        self.assert_rule_passed(sRuleId)

    def test_passes_when_configured_setup_requirement_is_above_by_less_than_rounding(self):
        # (40.0003 / 2) * 3 - 40.000 = 20.00045
        self.execute_with_capture_period(40.0003)

        self.assert_rule_passed(sRuleId)

    def test_passes_when_configured_setup_requirement_is_below_by_less_than_rounding(self):
        # (39.9997 / 2) * 3 - 40.000 = 19.99955
        self.execute_with_capture_period(39.9997)

        self.assert_rule_passed(sRuleId)

    def test_fails_when_configured_setup_requirement_is_above_by_more_than_rounding(self):
        # (40.0004 / 2) * 3 - 40.000 = 20.0006
        self.execute_with_capture_period(40.0004)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_configured_setup_requirement_is_below_by_more_than_rounding(self):
        # (39.9996 / 2) * 3 - 40.000 = 19.9994
        self.execute_with_capture_period(39.9996)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_one_setup_timing_report_has_a_different_requirement(self):
        self.execute_with_requirement_lines_changed([iSlowSetupRequirementLine], 'Requirement:            20.000ns', 'Requirement:            30.000ns')

        self.assert_rule_failed(sRuleId)

    def test_ignores_requirement_of_hold_timing_reports(self):
        self.execute_with_requirement_lines_changed(lHoldRequirementLines, 'Requirement:            -20.000ns', 'Requirement:            5.000ns')

        self.assert_rule_passed(sRuleId)

    def test_failure_lists_each_setup_timing_report_with_a_different_requirement(self):
        self.execute_with_edges(iPassingLaunchEdge, 'F', 'D')

        lExpected = []
        for iLineNumber in lSetupRequirementLines:
            lExpected.append(f'{sTimingReport}:{iLineNumber}  setup requirement 20.000ns, configured setup requirement 60.000ns')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)

    def test_failure_lists_only_the_setup_timing_report_with_a_different_requirement(self):
        self.execute_with_requirement_lines_changed([iSlowSetupRequirementLine], 'Requirement:            20.000ns', 'Requirement:            30.000ns')

        lExpected = []
        lExpected.append(f'{self.sChangedTimingReport}:{iSlowSetupRequirementLine}  setup requirement 30.000ns, configured setup requirement 20.000ns')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)
