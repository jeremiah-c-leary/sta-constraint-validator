
import unittest

from stacv import timing_model
from stacv import part
from stacv import board
from stacv import device
from stacv import interface

from tests import utils


class Test(unittest.TestCase):

    def setUp(self):

        self.oPart = part.new(utils.create_part_dict())
        self.oBoard = board.new(utils.create_board_dict())
        self.oDevice = device.new(utils.create_device_dict())


    def test_new_timing_model(self):

        oTM = timing_model.new('DAC_DATA', self.oDevice, self.oBoard, self.oPart)

        self.assertTrue(isinstance(oTM, timing_model.SourceSynchronousWithRoundTrip))
        self.assertTrue(isinstance(oTM.device_interface, interface.DeviceInterface))
        self.assertTrue(isinstance(oTM.part_interface, interface.PartInterface))
        self.assertEqual('serial_data', oTM.part_interface.name)
        self.assertTrue(isinstance(oTM.traces, board.Board))
