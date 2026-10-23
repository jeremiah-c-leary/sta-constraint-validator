
import unittest

from tests.rules.clock import clock_rule_test_case
from tests.rules.clock.clock_rule_test_case import fPassingLaunchFrequency
from tests.rules.clock.clock_rule_test_case import iLastReportLaunchClockLine
from tests.rules.clock.clock_rule_test_case import sPassingLaunchName

sRuleId = 's4_launch_clock_002'

# The launch clock period in every timing report is 10.000ns, which is 1000 / 100 MHz.


@unittest.skip('temp')
class Test(clock_rule_test_case.ClockRuleTestCase):

    def test_passes_when_launch_clock_period_matches_configured_frequency(self):
        self.execute_with_launch_clock(sPassingLaunchName, fPassingLaunchFrequency)

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_launch_clock_period_matches(self):
        iExitCode = self.execute_with_launch_clock(sPassingLaunchName, fPassingLaunchFrequency)

        self.assertEqual(0, iExitCode)

    def test_fails_when_configured_launch_clock_frequency_differs(self):
        # 1000 / 50 = 20.000ns
        self.execute_with_launch_clock(sPassingLaunchName, 50)

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_launch_clock_frequency_differs(self):
        iExitCode = self.execute_with_launch_clock(sPassingLaunchName, 50)

        self.assertEqual(1, iExitCode)

    def test_passes_when_expected_period_is_above_by_less_than_rounding(self):
        # 1000 / 99.996 = 10.0004ns
        self.execute_with_launch_clock(sPassingLaunchName, 99.996)

        self.assert_rule_passed(sRuleId)

    def test_passes_when_expected_period_is_below_by_less_than_rounding(self):
        # 1000 / 100.004 = 9.9996ns
        self.execute_with_launch_clock(sPassingLaunchName, 100.004)

        self.assert_rule_passed(sRuleId)

    def test_fails_when_expected_period_is_above_by_more_than_rounding(self):
        # 1000 / 99.994 = 10.0006ns
        self.execute_with_launch_clock(sPassingLaunchName, 99.994)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_expected_period_is_below_by_more_than_rounding(self):
        # 1000 / 100.006 = 9.9994ns
        self.execute_with_launch_clock(sPassingLaunchName, 100.006)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_one_timing_report_has_a_different_launch_clock_period(self):
        self.execute_with_last_report_line_changed(iLastReportLaunchClockLine, 'period=10.000ns', 'period=8.000ns')

        self.assert_rule_failed(sRuleId)

    def test_ignores_launch_clock_name(self):
        self.execute_with_launch_clock('clk_50mhz', fPassingLaunchFrequency)

        self.assert_rule_passed(sRuleId)
