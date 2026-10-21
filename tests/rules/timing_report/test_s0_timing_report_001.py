import os
import unittest

from stacv.timing_report import timing_report_file

from stacv.timing_report.xilinx import vivado

from stacv.rules.timing_report import s0_timing_report_001

from tests import utils

sTestDir = os.path.dirname(__file__)

oPassingFile = timing_report_file.TimingReportFile('s0_timing_report_001.passing.rpt', utils.read_file(os.path.join(sTestDir, 's0_timing_report_001.passing.rpt')))
oFailingFile = timing_report_file.TimingReportFile('s0_timing_report_001.failing.rpt', utils.read_file(os.path.join(sTestDir, 's0_timing_report_001.failing.rpt')))


class Test(unittest.TestCase):

    def test_passing_timing_reports(self):
        oTimingReports = vivado.parse_timing_report(oPassingFile)

        oRuleResult = s0_timing_report_001.check(utils.create_port_profile(oTimingReports))

        self.assertEqual('s0_timing_report_001', oRuleResult.rule_id)
        self.assertTrue(oRuleResult.is_passed())
        self.assertEqual([], oRuleResult.details)

    def test_failing_timing_reports(self):
        oTimingReports = vivado.parse_timing_report(oFailingFile)

        oRuleResult = s0_timing_report_001.check(utils.create_port_profile(oTimingReports))

        self.assertEqual('s0_timing_report_001', oRuleResult.rule_id)
        self.assertTrue(oRuleResult.is_failed())

    def test_failing_timing_reports_lists_setup_timing_reports_found(self):
        oTimingReports = vivado.parse_timing_report(oFailingFile)

        oRuleResult = s0_timing_report_001.check(utils.create_port_profile(oTimingReports))

        lExpected = []
        lExpected.append('s0_timing_report_001.failing.rpt:75  setup timing report, Fast process corner')

        self.assertEqual(lExpected, oRuleResult.details)
