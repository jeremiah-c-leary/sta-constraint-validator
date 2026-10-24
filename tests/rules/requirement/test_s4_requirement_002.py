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
    lText.append('interface = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append(f'launch_clock = {{name = "clk_100mhz", period = 10.000, setup_edge = 8, hold_edge = {oHoldEdges.launch_edge}}}')
    lText.append(f'capture_clock = {{port = "O_DAC_SCLK", name = "dac_sclk", period = {oHoldEdges.capture_period}, setup_edge = "C", hold_edge = "{oHoldEdges.capture_edge}"}}')
    lText.append(f'timing_reports = ["{sTimingReportFile}"]')
    return '\n'.join(lText)


def build_part_text():
    # With the traces below, the calculated output delays match sTimingReport:
    #    maximum:   0.5 + 2.0 - 0.5 = 2.000
    #    minimum:  -0.5 + 2.0 - 0.5 = 1.000
    lText = []
    lText.append('[properties]')
    lText.append('manufacturer = "Texas Instruments"')
    lText.append('part_number = "DAC81404"')
    lText.append('[datasheet]')
    lText.append('name = "DACx1401 Quad, 16-Bit and 12-Bit, High-Voltage-Output DACs With Internal Reference"')
    lText.append('url = "https://www.ti.com/lit/ds/symlink/dac81404.pdf"')
    lText.append('version = "SLASEH2A -- November 2020 -- REVISED MAY 2021"')
    lText.append('[[interface]]')
    lText.append('name = "Serial Interface"')
    lText.append('[[interface.pin]]')
    lText.append('name = "SDIN"')
    lText.append('methodology = "SDR-SS-I"')
    lText.append('clock = {pin = "SCLK", max_frequency = 25}')
    lText.append('capture_edge = "Rising"')
    lText.append('setup = {value = 0.5, symbol = "tSDIS", source = "Table 7.6"}')
    lText.append('hold = {value = 0.5, symbol = "tSDIH", source = "Table 7.6"}')
    return '\n'.join(lText)


def build_traces_text():
    lText = []
    lText.append('[[trace]]')
    lText.append('name = "data_output"')
    lText.append('device_pin = "O_DAC_DATA"')
    lText.append('part_pin = "SDIN"')
    lText.append('device_to_part = {max_delay = 2.0, min_delay = 2.0}')
    lText.append('[[trace]]')
    lText.append('name = "clock"')
    lText.append('device_pin = "O_DAC_SCLK"')
    lText.append('part_pin = "SCLK"')
    lText.append('device_to_part = {max_delay = 0.5, min_delay = 0.5}')
    return '\n'.join(lText)


def read_lines(sFilename):
    with open(sFilename) as oFile:
        return oFile.read().split('\n')


def write_file(sFilename, sText):
    with open(sFilename, 'w') as oFile:
        oFile.write(sText)


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
        lLines = read_lines(sTimingReport)
        for iLineNumber in lLineNumbers:
            self.assertIn(sOld, lLines[iLineNumber - 1])
            lLines[iLineNumber - 1] = lLines[iLineNumber - 1].replace(sOld, sNew)
        write_file(self.sChangedTimingReport, '\n'.join(lLines))
        oHoldEdges = HoldEdges(iLaunchEdge, sCaptureEdge, fPassingCapturePeriod)
        return self.execute(oHoldEdges, self.sChangedTimingReport)

    def execute(self, oHoldEdges, sTimingReportFile):
        write_file(self.sConfigFile, build_config_text(self.sPartFile, self.sTracesFile, sTimingReportFile, oHoldEdges))
        write_file(self.sPartFile, build_part_text())
        write_file(self.sTracesFile, build_traces_text())
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
        # (50.000 / 2) * 1 - (10.000 / 2) * 0 = 25.000 - 0.000 = 25.000
        self.execute_with_hold_edges(iPassingLaunchHoldEdge, 'B')

        self.assert_rule_failed(sRuleId)

    def test_fails_when_configured_hold_requirement_is_negative(self):
        # (50.000 / 2) * 1 - (10.000 / 2) * 8 = 25.000 - 40.000 = -15.000
        self.execute_with_hold_edges(8, 'B')

        self.assert_rule_failed(sRuleId)

    def test_passes_when_negative_hold_requirement_matches_configured_hold_edges(self):
        # (50.000 / 2) * 1 - (10.000 / 2) * 8 = 25.000 - 40.000 = -15.000
        self.execute_with_hold_edges_and_requirement_lines_changed(8, 'B', lHoldRequirementLines, 'Requirement:            0.000ns', 'Requirement:            -15.000ns')

        self.assert_rule_passed(sRuleId)

    def test_passes_when_a_later_pair_of_edges_has_the_same_hold_requirement(self):
        # (50.000 / 2) * 1 - (10.000 / 2) * 5 = 25.000 - 25.000 = 0.000
        self.execute_with_hold_edges(5, 'B')

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
        self.execute_with_hold_edges(8, 'B')

        lExpected = []
        for iLineNumber in lHoldRequirementLines:
            lExpected.append(f'{sTimingReport}:{iLineNumber}  hold requirement 0.000ns, configured hold requirement -15.000ns')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)

    def test_failure_lists_only_the_hold_timing_report_with_a_different_requirement(self):
        self.execute_with_requirement_lines_changed([165], 'Requirement:            0.000ns', 'Requirement:            5.000ns')

        lExpected = []
        lExpected.append(f'{self.sChangedTimingReport}:165  hold requirement 5.000ns, configured hold requirement 0.000ns')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)
