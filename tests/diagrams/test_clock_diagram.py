
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


    def test_text_renderer_100mhz_to_20mhz(self):

        lExpected = render_text_diagram_100mhz_to_20mhz()

        lActual = text_diagram.render(self.oTM, 'O_DAC_DATA')

        self.assertEqual(lExpected, lActual)


    def test_text_renderer_input_20mhz_to_100mhz(self):

        lExpected = render_text_diagram_20mhz_to_100mhz()

        lActual = text_diagram.render(self.oTM, 'I_DAC_DATA')

        self.assertEqual(lExpected, lActual)


    def test_text_renderer_input_100mhz_to_20mhz(self):

        lExpected = render_text_diagram_100mhz_to_50mhz()

        lActual = text_diagram.render(self.oTM, 'I_DEBUG')

        self.assertEqual(lExpected, lActual)


def render_text_diagram_100mhz_to_20mhz():
    lReturn = []
    lReturn.append('   __    __    __    __    __    __    __    __    __    __    ')
    lReturn.append('__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|')
    lReturn.append('')
    lReturn.append('   ______________                ______________                ')
    lReturn.append('__|              |______________|              |______________|')

    return lReturn 


def render_text_diagram_20mhz_to_100mhz():
    lReturn = []
    lReturn.append('   ______________                ______________                ')
    lReturn.append('__|              |______________|              |______________|')
    lReturn.append('')
    lReturn.append('   __    __    __    __    __    __    __    __    __    __    ')
    lReturn.append('__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|')

    return lReturn 


def render_text_diagram_100mhz_to_50mhz():
    lReturn = []
    lReturn.append('   __    __    __    __    ')
    lReturn.append('__|  |__|  |__|  |__|  |__|')
    lReturn.append('')
    lReturn.append('   _____       _____       ')
    lReturn.append('__|     |_____|     |_____|')

    return lReturn 
