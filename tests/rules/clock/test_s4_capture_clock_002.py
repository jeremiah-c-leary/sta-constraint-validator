
import unittest

from tests.rules.clock import clock_rule_test_case
from tests.rules.clock.clock_rule_test_case import fPassingCaptureFrequency
from tests.rules.clock.clock_rule_test_case import iLastReportCaptureClockLine
from tests.rules.clock.clock_rule_test_case import sPassingCaptureName

sRuleId = 's4_capture_clock_002'

# The capture clock period in every timing report is 50.000ns, which is 1000 / 20 MHz.


@unittest.skip('temp')
class Test(clock_rule_test_case.ClockRuleTestCase):

    def test_passes_when_capture_clock_period_matches_configured_frequency(self):
        self.execute_with_capture_clock(sPassingCaptureName, fPassingCaptureFrequency)

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_capture_clock_period_matches(self):
        iExitCode = self.execute_with_capture_clock(sPassingCaptureName, fPassingCaptureFrequency)

        self.assertEqual(0, iExitCode)

    def test_fails_when_configured_capture_clock_frequency_differs(self):
        # 1000 / 25 = 40.000ns
        self.execute_with_capture_clock(sPassingCaptureName, 25)

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_capture_clock_frequency_differs(self):
        iExitCode = self.execute_with_capture_clock(sPassingCaptureName, 25)

        self.assertEqual(1, iExitCode)

    def test_passes_when_expected_period_is_above_by_less_than_rounding(self):
        # 1000 / 19.99984 = 50.0004ns
        self.execute_with_capture_clock(sPassingCaptureName, 19.99984)

        self.assert_rule_passed(sRuleId)

    def test_passes_when_expected_period_is_below_by_less_than_rounding(self):
        # 1000 / 20.00016 = 49.9996ns
        self.execute_with_capture_clock(sPassingCaptureName, 20.00016)

        self.assert_rule_passed(sRuleId)

    def test_fails_when_expected_period_is_above_by_more_than_rounding(self):
        # 1000 / 19.99976 = 50.0006ns
        self.execute_with_capture_clock(sPassingCaptureName, 19.99976)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_expected_period_is_below_by_more_than_rounding(self):
        # 1000 / 20.00024 = 49.9994ns
        self.execute_with_capture_clock(sPassingCaptureName, 20.00024)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_one_timing_report_has_a_different_capture_clock_period(self):
        self.execute_with_last_report_line_changed(iLastReportCaptureClockLine, 'period=50.000ns', 'period=40.000ns')

        self.assert_rule_failed(sRuleId)

    def test_ignores_capture_clock_name(self):
        self.execute_with_capture_clock('spi_sclk', fPassingCaptureFrequency)

        self.assert_rule_passed(sRuleId)
