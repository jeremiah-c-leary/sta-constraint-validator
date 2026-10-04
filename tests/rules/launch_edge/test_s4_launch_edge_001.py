
import os
import unittest

from stacv.intent import timing_model
from stacv.intent import part
from stacv.intent import board
from stacv.intent import device

from stacv.timing_report import timing_report as tr

from stacv.timing_report.xilinx import vivado

from stacv.rules.launch_edge import s4_launch_edge_001 as Rule

from tests import utils

sTestDir = os.path.dirname(__file__)

lFile = utils.read_file(os.path.join(sTestDir, 's4_launch_edge_001.rpt'))


class Test(unittest.TestCase):

    def setUp(self):

        self.oPart = part.new(utils.create_part_dict())
        self.oBoard = board.new(utils.create_board_dict())
        self.oDevice = device.new(utils.create_device_dict())
        self.oTM = timing_model.new('DAC_DATA', self.oDevice, self.oBoard, self.oPart)
        lTimingReports = vivado.parse_timing_report(lFile)
        self.oTr = tr.new(lTimingReports[0])


    @unittest.skip('rewriting parser to return objects.  Remove when completed.')
    def test_failing_edges(self):

        self.assertFalse(Rule.check(self.oTr, self.oTM))

    @unittest.skip('rewriting parser to return objects.  Remove when completed.')
    def test_passing_edges(self):

        self.oTr.launch_edge = 25

        self.assertTrue(Rule.check(self.oTr, self.oTM))

