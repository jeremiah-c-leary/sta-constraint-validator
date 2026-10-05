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

        self.assertTrue(s2_output_delay_002.check(oTimingReports))

    def test_hold_output_delay_differs(self):
        oTimingReports = parse_test_report('s2_output_delay_002.failing.rpt')

        self.assertFalse(s2_output_delay_002.check(oTimingReports))

    def test_setup_output_delays_are_ignored(self):
        oTimingReports = parse_test_report('s2_output_delay_002.passing_setup_differs.rpt')

        self.assertTrue(s2_output_delay_002.check(oTimingReports))

    def test_empty_timing_report_list_passes(self):
        oTimingReports = timing_report_list.TimingReportList()

        self.assertTrue(s2_output_delay_002.check(oTimingReports))
