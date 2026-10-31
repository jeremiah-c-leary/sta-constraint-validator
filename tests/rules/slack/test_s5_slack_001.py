import os

from tests.rules import rule_test_case

sTestDir = os.path.dirname(os.path.abspath(__file__))
sParseDir = os.path.join(sTestDir, '..', '..', 'timing_report', 'parse', 'vivado')

# The setup timing reports in this file give a slack of 7.192ns on line 75 and 7.487ns on line 219.
# The hold timing reports give a slack of 0.272ns on line 14 and 0.513ns on line 158.
sTimingReport = os.path.abspath(os.path.join(sParseDir, 'O_DAC_DATA_timing.rpt'))
lSetupSlackLines = [75, 219]
lHoldSlackLines = [14, 158]

sRuleId = 's5_slack_001'

sNegativeSlack = 'Slack (VIOLATED) :        -0.012ns'
sZeroSlack = 'Slack (MET) :             0.000ns'

# A launch setup edge of 8 matches the setup requirement in sTimingReport, so stage 4 passes.
iPassingLaunchSetupEdge = 8


def build_config_text(sPartFile, sTracesFile, sTimingReportFile, iLaunchSetupEdge):
    lText = []
    lText.append('description = "s5_slack_001 test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[clock]]')
    lText.append('name = "clk_100mhz"')
    lText.append('period = 10.000')
    lText.append('[[clock]]')
    lText.append('name = "dac_sclk"')
    lText.append('period = 50.0')
    lText.append('port = "O_DAC_SCLK"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append(f'launch_clock = {{name = "clk_100mhz", setup_edge = {iLaunchSetupEdge}, hold_edge = 0}}')
    lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
    lText.append(f'timing_reports = ["{sTimingReportFile}"]')
    return '\n'.join(lText)


def replace_slack(sLine, sNewSlack):
    # Keeps the text after the slack value, for example '  (required time - arrival time)'.
    sAfterSlack = sLine[sLine.index('ns') + 2:]
    return sNewSlack + sAfterSlack


class Test(rule_test_case.RuleTestCase):

    def execute_with_slack_lines_changed(self, lLineNumbers, sNewSlack):
        return self.execute_with_launch_setup_edge_and_slack_lines_changed(iPassingLaunchSetupEdge, lLineNumbers, sNewSlack)

    def execute_with_launch_setup_edge_and_slack_lines_changed(self, iLaunchSetupEdge, lLineNumbers, sNewSlack):
        lLines = rule_test_case.read_lines(sTimingReport)
        for iLineNumber in lLineNumbers:
            self.assertTrue(lLines[iLineNumber - 1].startswith('Slack (MET) :'))
            lLines[iLineNumber - 1] = replace_slack(lLines[iLineNumber - 1], sNewSlack)
        rule_test_case.write_file(self.sChangedTimingReport, '\n'.join(lLines))
        return self.execute(iLaunchSetupEdge, self.sChangedTimingReport)

    def execute(self, iLaunchSetupEdge, sTimingReportFile):
        rule_test_case.write_file(self.sInterfaceFile, build_config_text(self.sPartFile, self.sTracesFile, sTimingReportFile, iLaunchSetupEdge))
        rule_test_case.write_file(self.sPartFile, rule_test_case.build_passing_part_text())
        rule_test_case.write_file(self.sTracesFile, rule_test_case.build_passing_traces_text())
        return self.run_check()

    def test_passes_when_setup_slack_is_positive(self):
        self.execute(iPassingLaunchSetupEdge, sTimingReport)

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_setup_slack_is_positive(self):
        iExitCode = self.execute(iPassingLaunchSetupEdge, sTimingReport)

        self.assertEqual(0, iExitCode)

    def test_passes_when_setup_slack_is_zero(self):
        self.execute_with_slack_lines_changed(lSetupSlackLines, sZeroSlack)

        self.assert_rule_passed(sRuleId)

    def test_fails_when_one_setup_slack_is_negative(self):
        self.execute_with_slack_lines_changed([219], sNegativeSlack)

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_setup_slack_is_negative(self):
        iExitCode = self.execute_with_slack_lines_changed([219], sNegativeSlack)

        self.assertEqual(1, iExitCode)

    def test_ignores_slack_of_hold_timing_reports(self):
        self.execute_with_slack_lines_changed(lHoldSlackLines, sNegativeSlack)

        self.assert_rule_passed(sRuleId)

    def test_is_skipped_when_a_stage_4_rule_fails(self):
        # A launch setup edge of 6 gives a setup requirement of 20.000ns, so s4_requirement_001 fails.
        self.execute_with_launch_setup_edge_and_slack_lines_changed(6, [219], sNegativeSlack)

        oSkipped = self.find_testcase(sRuleId).find('skipped')
        self.assertEqual('stage 4 failed', oSkipped.get('message'))

    def test_failure_lists_each_setup_timing_report_with_negative_slack(self):
        self.execute_with_slack_lines_changed(lSetupSlackLines, sNegativeSlack)

        lExpected = []
        for iLineNumber in lSetupSlackLines:
            lExpected.append(f'{self.sChangedTimingReport}:{iLineNumber}  setup slack -0.012ns')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)

    def test_failure_lists_only_the_setup_timing_report_with_negative_slack(self):
        self.execute_with_slack_lines_changed([219], sNegativeSlack)

        lExpected = []
        lExpected.append(f'{self.sChangedTimingReport}:219  setup slack -0.012ns')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)
