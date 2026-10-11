
import os
import unittest

from stacv.timing_report import timing_report_file

from stacv.timing_report.xilinx import vivado

from stacv.rules.clock import s1_clock_001

from tests import utils

sTestDir = os.path.dirname(__file__)

oPassingFile = timing_report_file.TimingReportFile('s1_clock_001.passing.rpt', utils.read_file(os.path.join(sTestDir, 's1_clock_001.passing.rpt')))
oFailingFile = timing_report_file.TimingReportFile('s1_clock_001.failing.rpt', utils.read_file(os.path.join(sTestDir, 's1_clock_001.failing.rpt')))


class Test(unittest.TestCase):

    def test_passing_timing_report(self):
        oTimingReports = vivado.parse_timing_report(oPassingFile)

        oRuleResult = s1_clock_001.check(oTimingReports.reports[0])

        self.assertEqual('s1_clock_001', oRuleResult.rule_id)
        self.assertTrue(oRuleResult.is_passed())
        self.assertEqual([], oRuleResult.details)

    def test_failing_timing_report(self):
        oTimingReports = vivado.parse_timing_report(oFailingFile)

        oRuleResult = s1_clock_001.check(oTimingReports.reports[0])

        self.assertEqual('s1_clock_001', oRuleResult.rule_id)
        self.assertFalse(oRuleResult.is_passed())

    def test_failing_timing_report_lists_both_start_points(self):
        oTimingReports = vivado.parse_timing_report(oFailingFile)

        oRuleResult = s1_clock_001.check(oTimingReports.reports[0])

        lExpected = []
        lExpected.append('s1_clock_001.failing.rpt:32  launch clock path starts at I_CLK')
        lExpected.append('s1_clock_001.failing.rpt:48  capture clock path starts at I_CLK2')

        self.assertEqual(lExpected, oRuleResult.details)
