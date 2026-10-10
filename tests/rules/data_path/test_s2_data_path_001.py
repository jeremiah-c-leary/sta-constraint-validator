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

        self.assertTrue(s2_data_path_001.check(oTimingReports).passed)

    def test_data_path_has_different_element(self):
        oTimingReports = parse_test_report('s2_data_path_001.failing_element.rpt')

        self.assertFalse(s2_data_path_001.check(oTimingReports).passed)

    def test_data_path_has_different_length(self):
        oTimingReports = parse_test_report('s2_data_path_001.failing_length.rpt')

        self.assertFalse(s2_data_path_001.check(oTimingReports).passed)

    def test_empty_timing_report_list_passes(self):
        oTimingReports = timing_report_list.TimingReportList()

        self.assertTrue(s2_data_path_001.check(oTimingReports).passed)
