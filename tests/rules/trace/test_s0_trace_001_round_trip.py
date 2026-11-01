from tests.rules import rule_test_case

sRuleId = 's0_trace_001'


class Test(rule_test_case.RoundTripRuleTestCase):

    def test_passes_when_the_data_trace_from_the_part_and_its_clock_trace_exist(self):
        self.execute_round_trip()

        self.assert_rule_passed(sRuleId)

    def test_fails_when_no_trace_from_the_part_ends_at_the_port(self):
        self.execute_round_trip(sTracesText=rule_test_case.build_round_trip_traces_text(bWithDataInput=False))

        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('a trace does not end with the port I_DAC_DATA', oFailure.text)
