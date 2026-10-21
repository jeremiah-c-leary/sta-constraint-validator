import os
import unittest

from stacv.timing_report import timing_report_file
from stacv.timing_report import timing_report_list

from stacv.timing_report.xilinx import vivado

from stacv.rules.data_path import s2_data_path_001

from tests import utils

sTestDir = os.path.dirname(__file__)


def parse_test_report(sFilename):
    sPath = os.path.join(sTestDir, sFilename)
    oFile = timing_report_file.TimingReportFile(sFilename, utils.read_file(sPath))
    return vivado.parse_timing_report(oFile)


class Test(unittest.TestCase):

    def test_data_paths_match(self):
        oTimingReports = parse_test_report('s2_data_path_001.passing.rpt')

        oRuleResult = s2_data_path_001.check(utils.create_port_profile(oTimingReports))

        self.assertEqual('s2_data_path_001', oRuleResult.rule_id)
        self.assertTrue(oRuleResult.is_passed())
        self.assertEqual([], oRuleResult.details)

    def test_data_path_has_different_element(self):
        oTimingReports = parse_test_report('s2_data_path_001.failing_element.rpt')

        oRuleResult = s2_data_path_001.check(utils.create_port_profile(oTimingReports))

        self.assertEqual('s2_data_path_001', oRuleResult.rule_id)
        self.assertFalse(oRuleResult.is_passed())

    def test_data_path_has_different_element_lists_every_timing_report(self):
        oTimingReports = parse_test_report('s2_data_path_001.failing_element.rpt')

        oRuleResult = s2_data_path_001.check(utils.create_port_profile(oTimingReports))

        lExpected = []
        lExpected.append('s2_data_path_001.failing_element.rpt:43  path 1')
        lExpected.append('s2_data_path_001.failing_element.rpt:109  path 1')
        lExpected.append('s2_data_path_001.failing_element.rpt:187  path 2')
        lExpected.append('s2_data_path_001.failing_element.rpt:253  path 1')

        self.assertEqual(lExpected, oRuleResult.details)

    def test_data_path_has_different_length(self):
        oTimingReports = parse_test_report('s2_data_path_001.failing_length.rpt')

        oRuleResult = s2_data_path_001.check(utils.create_port_profile(oTimingReports))

        self.assertFalse(oRuleResult.is_passed())

    def test_data_path_has_different_length_lists_every_timing_report(self):
        oTimingReports = parse_test_report('s2_data_path_001.failing_length.rpt')

        oRuleResult = s2_data_path_001.check(utils.create_port_profile(oTimingReports))

        lExpected = []
        lExpected.append('s2_data_path_001.failing_length.rpt:43  path 1')
        lExpected.append('s2_data_path_001.failing_length.rpt:109  path 1')
        lExpected.append('s2_data_path_001.failing_length.rpt:187  path 2')
        lExpected.append('s2_data_path_001.failing_length.rpt:250  path 1')

        self.assertEqual(lExpected, oRuleResult.details)

    def test_empty_timing_report_list_passes(self):
        oTimingReports = timing_report_list.TimingReportList()

        oRuleResult = s2_data_path_001.check(utils.create_port_profile(oTimingReports))

        self.assertTrue(oRuleResult.is_passed())
        self.assertEqual([], oRuleResult.details)
