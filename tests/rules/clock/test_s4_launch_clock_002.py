
import unittest

from tests.rules.clock import clock_rule_test_case
from tests.rules.clock.clock_rule_test_case import fPassingLaunchPeriod
from tests.rules.clock.clock_rule_test_case import iLastReportLaunchClockLine
from tests.rules.clock.clock_rule_test_case import sPassingLaunchName

sRuleId = 's4_launch_clock_002'

# The launch clock period in every timing report is 10.000ns.
# Periods within 0.0005ns of 10.000ns match, half of the last digit printed in the timing report.


@unittest.skip('temp')
class Test(clock_rule_test_case.ClockRuleTestCase):

    def test_passes_when_launch_clock_period_matches_configured_period(self):
        self.execute_with_launch_clock(sPassingLaunchName, fPassingLaunchPeriod)

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_launch_clock_period_matches(self):
        iExitCode = self.execute_with_launch_clock(sPassingLaunchName, fPassingLaunchPeriod)

        self.assertEqual(0, iExitCode)

    def test_fails_when_configured_launch_clock_period_differs(self):
        self.execute_with_launch_clock(sPassingLaunchName, 20.0)

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_launch_clock_period_differs(self):
        iExitCode = self.execute_with_launch_clock(sPassingLaunchName, 20.0)

        self.assertEqual(1, iExitCode)

    def test_passes_when_configured_period_is_above_by_less_than_rounding(self):
        self.execute_with_launch_clock(sPassingLaunchName, 10.0004)

        self.assert_rule_passed(sRuleId)

    def test_passes_when_configured_period_is_below_by_less_than_rounding(self):
        self.execute_with_launch_clock(sPassingLaunchName, 9.9996)

        self.assert_rule_passed(sRuleId)

    def test_fails_when_configured_period_is_above_by_more_than_rounding(self):
        self.execute_with_launch_clock(sPassingLaunchName, 10.0006)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_configured_period_is_below_by_more_than_rounding(self):
        self.execute_with_launch_clock(sPassingLaunchName, 9.9994)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_one_timing_report_has_a_different_launch_clock_period(self):
        self.execute_with_last_report_line_changed(iLastReportLaunchClockLine, 'period=10.000ns', 'period=8.000ns')

        self.assert_rule_failed(sRuleId)

    def test_ignores_launch_clock_name(self):
        self.execute_with_launch_clock('clk_50mhz', fPassingLaunchPeriod)

        self.assert_rule_passed(sRuleId)
