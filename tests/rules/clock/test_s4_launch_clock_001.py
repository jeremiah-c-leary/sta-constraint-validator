
import unittest

from tests.rules.clock import clock_rule_test_case
from tests.rules.clock.clock_rule_test_case import fPassingLaunchPeriod
from tests.rules.clock.clock_rule_test_case import iLastReportLaunchClockLine
from tests.rules.clock.clock_rule_test_case import sPassingLaunchName

sRuleId = 's4_launch_clock_001'


@unittest.skip('temp')
class Test(clock_rule_test_case.ClockRuleTestCase):

    def test_passes_when_launch_clock_name_matches_every_timing_report(self):
        self.execute_with_launch_clock(sPassingLaunchName, fPassingLaunchPeriod)

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_launch_clock_name_matches(self):
        iExitCode = self.execute_with_launch_clock(sPassingLaunchName, fPassingLaunchPeriod)

        self.assertEqual(0, iExitCode)

    def test_fails_when_configured_launch_clock_name_differs(self):
        self.execute_with_launch_clock('clk_50mhz', fPassingLaunchPeriod)

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_launch_clock_name_differs(self):
        iExitCode = self.execute_with_launch_clock('clk_50mhz', fPassingLaunchPeriod)

        self.assertEqual(1, iExitCode)

    def test_fails_when_launch_clock_name_differs_only_in_case(self):
        self.execute_with_launch_clock('CLK_100MHZ', fPassingLaunchPeriod)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_one_timing_report_has_a_different_launch_clock(self):
        self.execute_with_last_report_line_changed(iLastReportLaunchClockLine, 'clocked by clk_100mhz', 'clocked by clk_50mhz')

        self.assert_rule_failed(sRuleId)

    def test_ignores_launch_clock_period(self):
        self.execute_with_launch_clock(sPassingLaunchName, 20.0)

        self.assert_rule_passed(sRuleId)
