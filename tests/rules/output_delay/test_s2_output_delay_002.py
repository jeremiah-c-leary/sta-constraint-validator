import os
import unittest

from stacv.timing_report import timing_report_file
from stacv.timing_report import timing_report_list

from stacv.timing_report.xilinx import vivado

from stacv.rules.output_delay import s2_output_delay_002

from tests import utils

sTestDir = os.path.dirname(__file__)


def parse_test_report(sFilename):
    sPath = os.path.join(sTestDir, sFilename)
    oFile = timing_report_file.TimingReportFile(sFilename, utils.read_file(sPath))
    return vivado.parse_timing_report(oFile)


class Test(unittest.TestCase):

    def test_hold_output_delays_match(self):
        oTimingReports = parse_test_report('s2_output_delay_002.passing.rpt')

        oRuleResult = s2_output_delay_002.check(oTimingReports)

        self.assertEqual('s2_output_delay_002', oRuleResult.rule_id)
        self.assertTrue(oRuleResult.is_passed())
        self.assertEqual([], oRuleResult.details)

    def test_hold_output_delay_differs(self):
        oTimingReports = parse_test_report('s2_output_delay_002.failing.rpt')

        oRuleResult = s2_output_delay_002.check(oTimingReports)

        self.assertEqual('s2_output_delay_002', oRuleResult.rule_id)
        self.assertFalse(oRuleResult.is_passed())

    def test_hold_output_delay_differs_lists_every_hold_timing_report(self):
        oTimingReports = parse_test_report('s2_output_delay_002.failing.rpt')

        oRuleResult = s2_output_delay_002.check(oTimingReports)

        lExpected = []
        lExpected.append('s2_output_delay_002.failing.rpt:24  1.000ns')
        lExpected.append('s2_output_delay_002.failing.rpt:168  1.100ns')

        self.assertEqual(lExpected, oRuleResult.details)

    def test_setup_output_delays_are_ignored(self):
        oTimingReports = parse_test_report('s2_output_delay_002.passing_setup_differs.rpt')

        oRuleResult = s2_output_delay_002.check(oTimingReports)

        self.assertTrue(oRuleResult.is_passed())

    def test_empty_timing_report_list_passes(self):
        oTimingReports = timing_report_list.TimingReportList()

        oRuleResult = s2_output_delay_002.check(oTimingReports)

        self.assertTrue(oRuleResult.is_passed())
        self.assertEqual([], oRuleResult.details)
