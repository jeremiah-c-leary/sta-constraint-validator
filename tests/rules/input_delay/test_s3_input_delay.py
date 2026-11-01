from tests.rules import rule_test_case

# The timing reports give a setup input delay of 34.000ns on line 24 and a hold input delay of 1.000ns on line 101.
sTimingReport = rule_test_case.sRoundTripTimingReport
iSetupInputDelayLine = rule_test_case.build_setup_lines(rule_test_case.iInputDelayLine)[0]
iHoldInputDelayLine = rule_test_case.build_hold_lines(rule_test_case.iInputDelayLine)[0]


class TestMaximum(rule_test_case.RoundTripRuleTestCase):

    sRuleId = 's3_input_delay_001'

    def test_passes_when_the_maximum_input_delay_matches_the_calculation(self):
        self.execute_round_trip()

        self.assert_rule_passed(self.sRuleId)

    def test_exit_code_is_zero_when_every_rule_passes(self):
        self.assertEqual(0, self.execute_round_trip())

    def test_fails_when_the_data_trace_maximum_delay_differs(self):
        # 3.0 + 30 + 2.0 = 35.000
        self.execute_round_trip(sTracesText=rule_test_case.build_round_trip_traces_text(fDataMaxDelay=2.0))

        self.assert_rule_failed(self.sRuleId)

    def test_fails_when_the_part_clock_to_out_maximum_differs(self):
        # 3.0 + 25 + 1.0 = 29.000
        self.execute_round_trip(sPartText=rule_test_case.build_round_trip_part_text(fClockToOutMax=25.0))

        self.assert_rule_failed(self.sRuleId)

    def test_passes_when_within_rounding_of_the_calculation(self):
        # 3.0 + 30 + 1.0004 = 34.0004
        self.execute_round_trip(sTracesText=rule_test_case.build_round_trip_traces_text(fDataMaxDelay=1.0004))

        self.assert_rule_passed(self.sRuleId)

    def test_failure_names_the_calculated_and_the_actual_input_delay(self):
        self.execute_round_trip(sTracesText=rule_test_case.build_round_trip_traces_text(fDataMaxDelay=2.0))

        sExpected = f'{sTimingReport}:{iSetupInputDelayLine}  Calculated maximum input delay is 35.000ns while actual input delay is 34.000ns'
        self.assertEqual(sExpected, self.find_testcase(self.sRuleId).find('failure').text)


class TestMinimum(rule_test_case.RoundTripRuleTestCase):

    sRuleId = 's3_input_delay_002'

    def test_passes_when_the_minimum_input_delay_matches_the_calculation(self):
        self.execute_round_trip()

        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_the_data_trace_minimum_delay_differs(self):
        # 1.0 + 0 + 0.5 = 1.500
        self.execute_round_trip(sTracesText=rule_test_case.build_round_trip_traces_text(fDataMinDelay=0.5))

        self.assert_rule_failed(self.sRuleId)

    def test_fails_when_the_part_clock_to_out_minimum_differs(self):
        # 1.0 + 2 + 0.0 = 3.000
        self.execute_round_trip(sPartText=rule_test_case.build_round_trip_part_text(fClockToOutMin=2.0))

        self.assert_rule_failed(self.sRuleId)

    def test_failure_names_the_calculated_and_the_actual_input_delay(self):
        self.execute_round_trip(sTracesText=rule_test_case.build_round_trip_traces_text(fDataMinDelay=0.5))

        sExpected = f'{sTimingReport}:{iHoldInputDelayLine}  Calculated minimum input delay is 1.500ns while actual input delay is 1.000ns'
        self.assertEqual(sExpected, self.find_testcase(self.sRuleId).find('failure').text)
