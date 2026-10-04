
import os
import unittest

from stacv.timing_report import timing_report_file

from stacv.timing_report.xilinx import vivado

from stacv.rules.clock import s1_clock_001 as Rule

from tests import utils

sTestDir = os.path.dirname(__file__)

oPassingFile = timing_report_file.TimingReportFile('s1_clock_001.passing.rpt', utils.read_file(os.path.join(sTestDir, 's1_clock_001.passing.rpt')))
oFailingFile = timing_report_file.TimingReportFile('s1_clock_001.failing.rpt', utils.read_file(os.path.join(sTestDir, 's1_clock_001.failing.rpt')))


class Test(unittest.TestCase):

    def test_failing_timing_report(self):
        oTimingReports = vivado.parse_timing_report(oFailingFile)

        self.assertFalse(Rule.check(oTimingReports.reports[0]))

    def test_passing_timing_report(self):
        oTimingReports = vivado.parse_timing_report(oPassingFile)

        self.assertTrue(Rule.check(oTimingReports.reports[0]))
