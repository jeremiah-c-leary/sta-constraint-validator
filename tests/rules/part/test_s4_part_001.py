from tests.rules import rule_test_case

# Every timing report in this file times the falling edge of the capture clock dac_sclk.
# The requirements are on lines 21, 98, 175 and 252.
sTimingReport = rule_test_case.sTimingReport
lRequirementLines = rule_test_case.build_all_lines(rule_test_case.iRequirementLine)
iSetupRequirementLine = lRequirementLines[0]

sRuleId = 's4_part_001'


def build_config_text(sPartFile, sTracesFile, sTimingReportFile):
    lText = []
    lText.append('description = "s4_part_001 test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append('part_interface = "Serial Interface"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[clock]]')
    lText.append('name = "clk_100mhz"')
    lText.append('period = 10.000')
    lText.append('[[clock]]')
    lText.append('name = "dac_sclk"')
    lText.append('period = 40.0')
    lText.append('port = "O_DAC_SCLK"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 8}')
    lText.append('capture_clock = {name = "dac_sclk", setup_edge = "D", hold_edge = "B"}')
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
            self.assertIn('dac_sclk fall@', lLines[iLineNumber - 1])
            lLines[iLineNumber - 1] = lLines[iLineNumber - 1].replace('dac_sclk fall@', 'dac_sclk rise@')
        rule_test_case.write_file(self.sChangedTimingReport, '\n'.join(lLines))
        return self.execute(sCaptureEdge, self.sChangedTimingReport)

    def test_passes_when_part_captures_on_falling_edge_and_reports_time_falling_edge(self):
        self.execute('Falling', sTimingReport)

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_capture_clock_edge_type_matches(self):
        iExitCode = self.execute('Falling', sTimingReport)

        self.assertEqual(0, iExitCode)

    def test_fails_when_part_captures_on_rising_edge_and_reports_time_falling_edge(self):
        self.execute('Rising', sTimingReport)

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_capture_clock_edge_type_differs(self):
        iExitCode = self.execute('Rising', sTimingReport)

        self.assertEqual(1, iExitCode)

    def test_passes_when_part_captures_on_rising_edge_and_reports_time_rising_edge(self):
        self.execute_with_requirement_lines_changed('Rising', lRequirementLines)

        self.assert_rule_passed(sRuleId)

    def test_fails_when_part_captures_on_falling_edge_and_reports_time_rising_edge(self):
        self.execute_with_requirement_lines_changed('Falling', lRequirementLines)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_one_timing_report_times_a_different_edge_type(self):
        self.execute_with_requirement_lines_changed('Falling', [iSetupRequirementLine])

        self.assert_rule_failed(sRuleId)

    def test_failure_lists_each_timing_report_with_a_different_edge_type(self):
        self.execute('Rising', sTimingReport)

        lExpected = []
        for iLineNumber in lRequirementLines:
            lExpected.append(f'{sTimingReport}:{iLineNumber}  capture clock edge fall, part SDIN captures on Rising')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)

    def test_failure_lists_only_the_timing_report_with_a_different_edge_type(self):
        self.execute_with_requirement_lines_changed('Falling', [iSetupRequirementLine])

        lExpected = []
        lExpected.append(f'{self.sChangedTimingReport}:{iSetupRequirementLine}  capture clock edge rise, part SDIN captures on Falling')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)
