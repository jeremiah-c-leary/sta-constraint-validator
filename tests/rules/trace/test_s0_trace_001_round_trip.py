from tests.rules import rule_test_case

sRuleId = 's0_trace_001'


class Test(rule_test_case.RoundTripRuleTestCase):

    def test_passes_when_the_data_trace_from_the_part_and_its_clock_trace_exist(self):
        self.execute_round_trip()

        self.assert_rule_passed(sRuleId)

    def test_fails_when_no_trace_from_the_part_ends_at_the_port(self):
        # SDO's trace ends at a deferred port, so the part's pins all have ports and only I_DAC_DATA has no trace.
        sTracesText = rule_test_case.build_round_trip_traces_text().replace('device_pin = "I_DAC_DATA"', 'device_pin = "I_SPARE_DATA"')
        self.execute_round_trip(sTracesText=sTracesText, sOtherPorts='[[port]]\nstatus = "defer"\nname = "I_SPARE_DATA"')

        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('a trace does not end with the port I_DAC_DATA', oFailure.text)
