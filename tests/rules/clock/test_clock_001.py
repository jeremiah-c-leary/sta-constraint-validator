
import os
import unittest

from stacv.timing_report import timing_report as tr

from stacv.timing_report.xilinx import vivado

from stacv.rules.clock import clock_001

from tests import utils

sTestDir = os.path.dirname(__file__)

lPassingFile = utils.read_file(os.path.join(sTestDir, 'clock_001.passing.rpt'))
lFailingFile = utils.read_file(os.path.join(sTestDir, 'clock_001.failing.rpt'))


class Test(unittest.TestCase):

    @unittest.skip('rewriting parser to return objects.  Remove when completed.')
    def test_failing_timing_report(self):

        lTimingReports = vivado.parse_timing_report(lFailingFile)
        oTr = tr.new(lTimingReports[0])

        self.assertFalse(clock_001.check(oTr))

    @unittest.skip('rewriting parser to return objects.  Remove when completed.')
    def test_passing_timing_report(self):

        lTimingReports = vivado.parse_timing_report(lPassingFile)
        oTr = tr.new(lTimingReports[0])

        self.assertTrue(clock_001.check(oTr))
