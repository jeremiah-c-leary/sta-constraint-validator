
import unittest

from tests.rules.clock import clock_rule_test_case
from tests.rules.clock.clock_rule_test_case import fPassingCapturePeriod
from tests.rules.clock.clock_rule_test_case import iFirstReportCaptureClockLine
from tests.rules.clock.clock_rule_test_case import sPassingCaptureName

sRuleId = 's4_capture_clock_002'

# The capture clock period in every timing report is 40.000ns.
# Periods within 0.0005ns of 40.000ns match, half of the last digit printed in the timing report.


class Test(clock_rule_test_case.ClockRuleTestCase):

    def test_passes_when_capture_clock_period_matches_configured_period(self):
        self.execute_with_capture_clock(sPassingCaptureName, fPassingCapturePeriod)

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_capture_clock_period_matches(self):
        iExitCode = self.execute_with_capture_clock(sPassingCaptureName, fPassingCapturePeriod)

        self.assertEqual(0, iExitCode)

    def test_fails_when_configured_capture_clock_period_differs(self):
        self.execute_with_capture_clock(sPassingCaptureName, 50.0)

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_capture_clock_period_differs(self):
        iExitCode = self.execute_with_capture_clock(sPassingCaptureName, 50.0)

        self.assertEqual(1, iExitCode)

    def test_passes_when_configured_period_is_above_by_less_than_rounding(self):
        self.execute_with_capture_clock(sPassingCaptureName, 40.0004)

        self.assert_rule_passed(sRuleId)

    def test_passes_when_configured_period_is_below_by_less_than_rounding(self):
        self.execute_with_capture_clock(sPassingCaptureName, 39.9996)

        self.assert_rule_passed(sRuleId)

    def test_fails_when_configured_period_is_above_by_more_than_rounding(self):
        self.execute_with_capture_clock(sPassingCaptureName, 40.0006)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_configured_period_is_below_by_more_than_rounding(self):
        self.execute_with_capture_clock(sPassingCaptureName, 39.9994)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_one_timing_report_has_a_different_capture_clock_period(self):
        self.execute_with_first_report_line_changed(iFirstReportCaptureClockLine, 'period=40.000ns', 'period=50.000ns')

        self.assert_rule_failed(sRuleId)

    def test_ignores_capture_clock_name(self):
        self.execute_with_capture_clock('spi_sclk', fPassingCapturePeriod)

        self.assert_rule_passed(sRuleId)
