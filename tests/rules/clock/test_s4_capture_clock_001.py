
import unittest

from tests.rules.clock import clock_rule_test_case
from tests.rules.clock.clock_rule_test_case import fPassingCaptureFrequency
from tests.rules.clock.clock_rule_test_case import iLastReportCaptureClockLine
from tests.rules.clock.clock_rule_test_case import sPassingCaptureName

sRuleId = 's4_capture_clock_001'

@unittest.skip('temp')
class Test(clock_rule_test_case.ClockRuleTestCase):

    def test_passes_when_capture_clock_name_matches_every_timing_report(self):
        self.execute_with_capture_clock(sPassingCaptureName, fPassingCaptureFrequency)

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_capture_clock_name_matches(self):
        iExitCode = self.execute_with_capture_clock(sPassingCaptureName, fPassingCaptureFrequency)

        self.assertEqual(0, iExitCode)

    def test_fails_when_configured_capture_clock_name_differs(self):
        self.execute_with_capture_clock('spi_sclk', fPassingCaptureFrequency)

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_capture_clock_name_differs(self):
        iExitCode = self.execute_with_capture_clock('spi_sclk', fPassingCaptureFrequency)

        self.assertEqual(1, iExitCode)

    def test_fails_when_capture_clock_name_differs_only_in_case(self):
        self.execute_with_capture_clock('DAC_SCLK', fPassingCaptureFrequency)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_one_timing_report_has_a_different_capture_clock(self):
        self.execute_with_last_report_line_changed(iLastReportCaptureClockLine, 'clocked by dac_sclk', 'clocked by spi_sclk')

        self.assert_rule_failed(sRuleId)

    def test_ignores_capture_clock_frequency(self):
        self.execute_with_capture_clock(sPassingCaptureName, 25)

        self.assert_rule_passed(sRuleId)
