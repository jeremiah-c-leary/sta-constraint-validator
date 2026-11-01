from tests.rules import rule_test_case

# The launch clock path of every timing report in this file ends at O_DAC_SCLK.
# The last element of each launch clock path, the net to the clock port, is on lines 48, 125, 202 and 279.
# Lines 48 and 202 are in setup timing reports, lines 125 and 279 in hold timing reports.
sTimingReport = rule_test_case.sRoundTripTimingReport
lLaunchClockPathEndLines = rule_test_case.build_all_lines(rule_test_case.iLaunchClockPathEndLine)
iSetupLaunchClockPathEndLine = lLaunchClockPathEndLines[0]
iHoldLaunchClockPathEndLine = lLaunchClockPathEndLines[1]

sRuleId = 's0_clock_path_002'


class Test(rule_test_case.RoundTripRuleTestCase):

    def execute_with_launch_clock_path_ends_changed(self, lLineNumbers):
        return self.execute_round_trip_with_lines_changed(lLineNumbers, 'O_DAC_SCLK', 'O_DAC_OTHER')

    def test_passes_when_launch_clock_path_ends_at_configured_clock_port(self):
        self.execute_round_trip()

        self.assert_rule_passed(sRuleId)

    def test_fails_when_configured_clock_port_differs(self):
        self.execute_round_trip(sClockPort='O_DAC_CSF')

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_launch_clock_path_ends_elsewhere(self):
        iExitCode = self.execute_with_launch_clock_path_ends_changed(lLaunchClockPathEndLines)

        self.assertEqual(1, iExitCode)

    def test_fails_when_launch_clock_path_of_one_setup_timing_report_ends_elsewhere(self):
        self.execute_with_launch_clock_path_ends_changed([iSetupLaunchClockPathEndLine])

        self.assert_rule_failed(sRuleId)

    def test_fails_when_launch_clock_path_of_one_hold_timing_report_ends_elsewhere(self):
        self.execute_with_launch_clock_path_ends_changed([iHoldLaunchClockPathEndLine])

        self.assert_rule_failed(sRuleId)

    def test_failure_lists_each_timing_report_whose_launch_clock_path_ends_elsewhere(self):
        self.execute_round_trip(sClockPort='O_DAC_CSF')

        lExpected = []
        for iLineNumber in lLaunchClockPathEndLines:
            lExpected.append(f'{sTimingReport}:{iLineNumber}  launch clock path ends at O_DAC_SCLK, configured clock port O_DAC_CSF')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)
