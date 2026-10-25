import os

from tests.rules import rule_test_case

sTestDir = os.path.dirname(os.path.abspath(__file__))
sParseDir = os.path.join(sTestDir, '..', '..', 'timing_report', 'parse', 'vivado')

# Every timing report in this file times the rising edge of the capture clock dac_sclk.
# The requirements are on lines 21, 82, 165 and 226.
sTimingReport = os.path.abspath(os.path.join(sParseDir, 'O_DAC_DATA_timing.rpt'))
lRequirementLines = [21, 82, 165, 226]

sRuleId = 's4_part_001'


def build_config_text(sPartFile, sTracesFile, sTimingReportFile):
    lText = []
    lText.append('description = "s4_part_001 test"')
    lText.append('interface = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append('launch_clock = {name = "clk_100mhz", period = 10.000, setup_edge = 8, hold_edge = 0}')
    lText.append('capture_clock = {port = "O_DAC_SCLK", name = "dac_sclk", period = 50, setup_edge = "C", hold_edge = "A"}')
    lText.append(f'timing_reports = ["{sTimingReportFile}"]')
    return '\n'.join(lText)


class Test(rule_test_case.RuleTestCase):

    def execute(self, sCaptureEdge, sTimingReportFile):
        rule_test_case.write_file(self.sInterfaceFile, build_config_text(self.sPartFile, self.sTracesFile, sTimingReportFile))
        rule_test_case.write_file(self.sPartFile, rule_test_case.build_part_text(sCaptureEdge, rule_test_case.fPassingSetup, rule_test_case.fPassingHold))
        rule_test_case.write_file(self.sTracesFile, rule_test_case.build_passing_traces_text())
        return self.run_check()

    def execute_with_requirement_lines_changed(self, sCaptureEdge, lLineNumbers):
        lLines = rule_test_case.read_lines(sTimingReport)
        for iLineNumber in lLineNumbers:
            self.assertIn('dac_sclk rise@', lLines[iLineNumber - 1])
            lLines[iLineNumber - 1] = lLines[iLineNumber - 1].replace('dac_sclk rise@', 'dac_sclk fall@')
        rule_test_case.write_file(self.sChangedTimingReport, '\n'.join(lLines))
        return self.execute(sCaptureEdge, self.sChangedTimingReport)

    def test_passes_when_part_captures_on_rising_edge_and_reports_time_rising_edge(self):
        self.execute('Rising', sTimingReport)

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_capture_clock_edge_type_matches(self):
        iExitCode = self.execute('Rising', sTimingReport)

        self.assertEqual(0, iExitCode)

    def test_fails_when_part_captures_on_falling_edge_and_reports_time_rising_edge(self):
        self.execute('Falling', sTimingReport)

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_capture_clock_edge_type_differs(self):
        iExitCode = self.execute('Falling', sTimingReport)

        self.assertEqual(1, iExitCode)

    def test_passes_when_part_captures_on_falling_edge_and_reports_time_falling_edge(self):
        self.execute_with_requirement_lines_changed('Falling', lRequirementLines)

        self.assert_rule_passed(sRuleId)

    def test_fails_when_part_captures_on_rising_edge_and_reports_time_falling_edge(self):
        self.execute_with_requirement_lines_changed('Rising', lRequirementLines)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_one_timing_report_times_a_different_edge_type(self):
        self.execute_with_requirement_lines_changed('Rising', [226])

        self.assert_rule_failed(sRuleId)

    def test_failure_lists_each_timing_report_with_a_different_edge_type(self):
        self.execute('Falling', sTimingReport)

        lExpected = []
        for iLineNumber in lRequirementLines:
            lExpected.append(f'{sTimingReport}:{iLineNumber}  capture clock edge rise, part SDIN captures on Falling')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)

    def test_failure_lists_only_the_timing_report_with_a_different_edge_type(self):
        self.execute_with_requirement_lines_changed('Rising', [226])

        lExpected = []
        lExpected.append(f'{self.sChangedTimingReport}:226  capture clock edge fall, part SDIN captures on Rising')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)
