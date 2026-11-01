from tests.rules import rule_test_case

# Every timing report in this file launches on the rising edge of dac_sclk_rd: its requirement is on lines 21, 98, 175 and 252.
sTimingReport = rule_test_case.sRoundTripTimingReport
lRequirementLines = rule_test_case.build_all_lines(rule_test_case.iRoundTripRequirementLine)

sRuleId = 's4_part_002'


class Test(rule_test_case.RoundTripRuleTestCase):

    def test_passes_when_the_launch_clock_edge_is_the_edge_the_part_launches_on(self):
        self.execute_round_trip()

        self.assert_rule_passed(sRuleId)

    def test_fails_when_the_part_launches_on_the_other_edge(self):
        self.execute_round_trip(sPartText=rule_test_case.build_round_trip_part_text(sLaunchEdge='Falling'))

        self.assert_rule_failed(sRuleId)

    def test_fails_when_one_timing_report_launches_on_the_other_edge(self):
        self.execute_round_trip_with_lines_changed(lRequirementLines[:1], 'dac_sclk_rd rise@0.000ns', 'dac_sclk_rd fall@0.000ns')

        self.assert_rule_failed(sRuleId)

    def test_failure_lists_each_timing_report_launching_on_the_other_edge(self):
        self.execute_round_trip(sPartText=rule_test_case.build_round_trip_part_text(sLaunchEdge='Falling'))

        lExpected = []
        for iLineNumber in lRequirementLines:
            lExpected.append(f'{sTimingReport}:{iLineNumber}  launch clock edge rise, part SDO launches on Falling')
        self.assertEqual('\n'.join(lExpected), self.find_testcase(sRuleId).find('failure').text)
