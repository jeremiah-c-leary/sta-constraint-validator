
import os
import unittest

from stacv import timing_model
from stacv import part
from stacv import board
from stacv import device

from stacv.timing_report import timing_report as tr

from stacv.timing_report.xilinx import vivado

from stacv.validate.clock import clock_002

from tests import utils

sTestDir = os.path.dirname(__file__)

lFile = utils.read_file(os.path.join(sTestDir, 'clock_002.rpt'))


class Test(unittest.TestCase):

    def setUp(self):

        self.oPart = part.new(utils.create_part_dict())
        self.oBoard = board.new(utils.create_board_dict())
        self.oDevice = device.new(utils.create_device_dict())
        self.oTM = timing_model.new('DAC_DATA', self.oDevice, self.oBoard, self.oPart)
        lTimingReports = vivado.parse_timing_report(lFile)
        self.oTr = tr.new(lTimingReports[0])


    def test_failing_edges(self):

        self.assertFalse(clock_002.check(self.oTr, self.oTM))

    def test_passing_edges(self):

        self.oTr.launch_edge = 25

        self.assertTrue(clock_002.check(self.oTr, self.oTM))

