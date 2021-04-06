
import unittest

from stacv import timing_model
from stacv import part
from stacv import board
from stacv import device
from stacv.diagram.clock import text_diagram

from tests import utils


class Test(unittest.TestCase):

    def setUp(self):

        self.oPart = part.new(utils.create_part_dict())
        self.oBoard = board.new(utils.create_board_dict())
        self.oDevice = device.new(utils.create_device_dict())
        self.oTM = timing_model.new('DAC_DATA', self.oDevice, self.oBoard, self.oPart)


    def test_text_renderer(self):

        lExpected = render_text_diagram()

        lActual = text_diagram.render(self.oTM, 'O_DAC_DATA')

        self.assertEqual(lExpected, lActual)


def render_text_diagram():
    lReturn = []
    lReturn.append('   __    __    __    __    __    __    __    __    __    __    ')
    lReturn.append('__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|')
    lReturn.append('')
    lReturn.append('   ______________                ______________                ')
    lReturn.append('__|              |______________|              |______________|')

    return lReturn 
