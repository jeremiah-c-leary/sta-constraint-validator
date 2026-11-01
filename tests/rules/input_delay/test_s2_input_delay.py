from tests.rules import rule_test_case

# Every setup timing report in this file has an input delay of 34.000ns, on lines 24 and 178.
# Every hold timing report has an input delay of 1.000ns, on lines 101 and 255.
lSetupInputDelayLines = rule_test_case.build_setup_lines(rule_test_case.iInputDelayLine)
lHoldInputDelayLines = rule_test_case.build_hold_lines(rule_test_case.iInputDelayLine)
sSetupInputDelay = 'Input Delay:            34.000ns'
sHoldInputDelay = 'Input Delay:            1.000ns'


class TestSetup(rule_test_case.RoundTripRuleTestCase):

    sRuleId = 's2_input_delay_001'

    def test_passes_when_every_setup_input_delay_is_the_same(self):
        self.execute_round_trip()

        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_one_setup_input_delay_differs(self):
        self.execute_round_trip_with_lines_changed(lSetupInputDelayLines[1:], sSetupInputDelay, 'Input Delay:            35.000ns')

        self.assert_rule_failed(self.sRuleId)

    def test_ignores_the_input_delays_of_hold_timing_reports(self):
        self.execute_round_trip_with_lines_changed(lHoldInputDelayLines[1:], sHoldInputDelay, 'Input Delay:            2.000ns')

        self.assert_rule_passed(self.sRuleId)

    def test_failure_lists_the_input_delay_of_every_setup_timing_report(self):
        self.execute_round_trip_with_lines_changed(lSetupInputDelayLines[1:], sSetupInputDelay, 'Input Delay:            35.000ns')

        lExpected = []
        lExpected.append(f'{self.sChangedTimingReport}:{lSetupInputDelayLines[0]}  34.000ns')
        lExpected.append(f'{self.sChangedTimingReport}:{lSetupInputDelayLines[1]}  35.000ns')
        oFailure = self.find_testcase(self.sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)


class TestHold(rule_test_case.RoundTripRuleTestCase):

    sRuleId = 's2_input_delay_002'

    def test_passes_when_every_hold_input_delay_is_the_same(self):
        self.execute_round_trip()

        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_one_hold_input_delay_differs(self):
        self.execute_round_trip_with_lines_changed(lHoldInputDelayLines[1:], sHoldInputDelay, 'Input Delay:            2.000ns')

        self.assert_rule_failed(self.sRuleId)

    def test_ignores_the_input_delays_of_setup_timing_reports(self):
        self.execute_round_trip_with_lines_changed(lSetupInputDelayLines[1:], sSetupInputDelay, 'Input Delay:            35.000ns')

        self.assert_rule_passed(self.sRuleId)

    def test_failure_lists_the_input_delay_of_every_hold_timing_report(self):
        self.execute_round_trip_with_lines_changed(lHoldInputDelayLines[1:], sHoldInputDelay, 'Input Delay:            2.000ns')

        lExpected = []
        lExpected.append(f'{self.sChangedTimingReport}:{lHoldInputDelayLines[0]}  1.000ns')
        lExpected.append(f'{self.sChangedTimingReport}:{lHoldInputDelayLines[1]}  2.000ns')
        oFailure = self.find_testcase(self.sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)
