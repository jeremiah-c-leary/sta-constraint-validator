from tests.rules import rule_test_case

# The data path of every timing report in this file starts at I_DAC_DATA.
# The first element of each data path, the net from the port, is on lines 52, 129, 206 and 283.
# Lines 52 and 206 are in setup timing reports, lines 129 and 283 in hold timing reports.
sTimingReport = rule_test_case.sRoundTripTimingReport
lDataPathStartLines = rule_test_case.build_all_lines(rule_test_case.iDataPathStartLine)
iSetupDataPathStartLine = lDataPathStartLines[0]
iHoldDataPathStartLine = lDataPathStartLines[1]

sRuleId = 's0_data_path_002'


class Test(rule_test_case.RoundTripRuleTestCase):

    def execute_with_data_path_starts_changed(self, lLineNumbers):
        # The port's row, on the line before, and the net from the port both name the port.
        lLines = []
        for iLineNumber in lLineNumbers:
            lLines.extend([iLineNumber - 1, iLineNumber])
        return self.execute_round_trip_with_lines_changed(lLines, 'I_DAC_DATA', 'I_DAC_OTHER')

    def test_passes_when_data_path_starts_at_configured_port(self):
        self.execute_round_trip()

        self.assert_rule_passed(sRuleId)

    def test_fails_when_configured_port_differs(self):
        self.execute_round_trip(sPortName='I_DAC_SDO')

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_data_path_starts_elsewhere(self):
        iExitCode = self.execute_with_data_path_starts_changed(lDataPathStartLines)

        self.assertEqual(1, iExitCode)

    def test_fails_when_data_path_of_one_setup_timing_report_starts_elsewhere(self):
        self.execute_with_data_path_starts_changed([iSetupDataPathStartLine])

        self.assert_rule_failed(sRuleId)

    def test_fails_when_data_path_of_one_hold_timing_report_starts_elsewhere(self):
        self.execute_with_data_path_starts_changed([iHoldDataPathStartLine])

        self.assert_rule_failed(sRuleId)

    def test_skips_stage_3_when_data_path_starts_elsewhere(self):
        self.execute_with_data_path_starts_changed(lDataPathStartLines)

        oSkipped = self.find_testcase('s3_input_delay_001').find('skipped')
        self.assertEqual('stage 0 failed', oSkipped.get('message'))

    def test_failure_lists_only_the_timing_report_whose_data_path_starts_elsewhere(self):
        self.execute_with_data_path_starts_changed([iSetupDataPathStartLine])

        lExpected = []
        lExpected.append(f'{self.sChangedTimingReport}:{iSetupDataPathStartLine}  data path starts at I_DAC_OTHER, configured port I_DAC_DATA')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)
