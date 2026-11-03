from tests.rules import rule_test_case


# The setup timing reports in this file give a slack of 7.524ns on line 14 and 7.260ns on line 168.
# The hold timing reports give a slack of 7.438ns on line 91 and 7.167ns on line 245.
sTimingReport = rule_test_case.sTimingReport
lSetupSlackLines = rule_test_case.build_setup_lines(rule_test_case.iSlackLine)
lHoldSlackLines = rule_test_case.build_hold_lines(rule_test_case.iSlackLine)
iSlowSetupSlackLine = lSetupSlackLines[0]
iSlowHoldSlackLine = lHoldSlackLines[0]

sRuleId = 's5_slack_002'

sNegativeSlack = 'Slack (VIOLATED) :        -0.012ns'
sZeroSlack = 'Slack (MET) :             0.000ns'

# A launch edge of 8 matches the hold requirement in sTimingReport, so stage 4 passes.
iPassingLaunchEdge = 8


def build_config_text(sPartFile, sTracesFile, sTimingReportFile, iLaunchEdge):
    lText = []
    lText.append('description = "s5_slack_002 test"')
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
    lText.append(f'launch_clock = {{name = "clk_100mhz", setup_edge = {iLaunchEdge}, hold_edge = {iLaunchEdge}}}')
    lText.append('capture_clock = {name = "dac_sclk", setup_edge = "D", hold_edge = "B"}')
    lText.append(f'timing_reports = ["{sTimingReportFile}"]')
    return '\n'.join(lText)


def replace_slack(sLine, sNewSlack):
    # Keeps the text after the slack value, for example '  (arrival time - required time)'.
    sAfterSlack = sLine[sLine.index('ns') + 2:]
    return sNewSlack + sAfterSlack


class Test(rule_test_case.RuleTestCase):

    def execute_with_slack_lines_changed(self, lLineNumbers, sNewSlack):
        return self.execute_with_launch_edge_and_slack_lines_changed(iPassingLaunchEdge, lLineNumbers, sNewSlack)

    def execute_with_launch_edge_and_slack_lines_changed(self, iLaunchEdge, lLineNumbers, sNewSlack):
        lLines = rule_test_case.read_lines(sTimingReport)
        for iLineNumber in lLineNumbers:
            self.assertTrue(lLines[iLineNumber - 1].startswith('Slack (MET) :'))
            lLines[iLineNumber - 1] = replace_slack(lLines[iLineNumber - 1], sNewSlack)
        rule_test_case.write_file(self.sChangedTimingReport, '\n'.join(lLines))
        return self.execute(iLaunchEdge, self.sChangedTimingReport)

    def execute(self, iLaunchEdge, sTimingReportFile):
        rule_test_case.write_file(self.sInterfaceFile, build_config_text(self.sPartFile, self.sTracesFile, sTimingReportFile, iLaunchEdge))
        rule_test_case.write_file(self.sPartFile, rule_test_case.build_passing_part_text())
        rule_test_case.write_file(self.sTracesFile, rule_test_case.build_passing_traces_text())
        return self.run_check()

    def test_passes_when_hold_slack_is_positive(self):
        self.execute(iPassingLaunchEdge, sTimingReport)

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_hold_slack_is_positive(self):
        iExitCode = self.execute(iPassingLaunchEdge, sTimingReport)

        self.assertEqual(0, iExitCode)

    def test_passes_when_hold_slack_is_zero(self):
        self.execute_with_slack_lines_changed(lHoldSlackLines, sZeroSlack)

        self.assert_rule_passed(sRuleId)

    def test_fails_when_one_hold_slack_is_negative(self):
        self.execute_with_slack_lines_changed([iSlowHoldSlackLine], sNegativeSlack)

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_hold_slack_is_negative(self):
        iExitCode = self.execute_with_slack_lines_changed([iSlowHoldSlackLine], sNegativeSlack)

        self.assertEqual(1, iExitCode)

    def test_ignores_slack_of_setup_timing_reports(self):
        self.execute_with_slack_lines_changed(lSetupSlackLines, sNegativeSlack)

        self.assert_rule_passed(sRuleId)

    def test_is_skipped_when_a_stage_4_rule_fails(self):
        # A launch edge of 2 gives a hold requirement of 10.000ns, so s4_requirement_002 fails.
        self.execute_with_launch_edge_and_slack_lines_changed(2, [iSlowHoldSlackLine], sNegativeSlack)

        oSkipped = self.find_testcase(sRuleId).find('skipped')
        self.assertEqual('stage 4 failed', oSkipped.get('message'))

    def test_failure_lists_each_hold_timing_report_with_negative_slack(self):
        self.execute_with_slack_lines_changed(lHoldSlackLines, sNegativeSlack)

        lExpected = []
        for iLineNumber in lHoldSlackLines:
            lExpected.append(f'{self.sChangedTimingReport}:{iLineNumber}  hold slack -0.012ns')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)

    def test_failure_lists_only_the_hold_timing_report_with_negative_slack(self):
        self.execute_with_slack_lines_changed([iSlowHoldSlackLine], sNegativeSlack)

        lExpected = []
        lExpected.append(f'{self.sChangedTimingReport}:{iSlowHoldSlackLine}  hold slack -0.012ns')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)
