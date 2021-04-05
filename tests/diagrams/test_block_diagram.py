
import unittest

from stacv import timing_model
from stacv import part
from stacv import board
from stacv import device
from stacv.diagram import block_diagram

from tests import utils


class Test(unittest.TestCase):

    def setUp(self):

        self.oPart = part.new(utils.create_part_dict())
        self.oBoard = board.new(utils.create_board_dict())
        self.oDevice = device.new(utils.create_device_dict())
        self.oTM = timing_model.new('DAC_DATA', self.oDevice, self.oBoard, self.oPart)


    def test_new_timing_model(self):

        dExpected = generate_block_diagram_dictionary()

        self.assertEqual(dExpected, block_diagram.extract_data_structure(self.oTM))


    def test_text_renderer(self):

        lExpected = render_text_diagram()

        lActual = block_diagram.render_text_diagram(self.oTM)

        self.assertEqual(lExpected, lActual)


def generate_block_diagram_dictionary():
    dReturn = {}

    dReturn['device'] = {}
    dReturn['device']['name'] = 'Arria10'
    dReturn['part'] = {}
    dReturn['part']['name'] = 'DAC81404'

    dReturn['traces'] = []

    dTrace = {}
    dTrace['device_pin'] = 'I_DAC_DATA'
    dTrace['part_pin'] = 'SDO'
    dTrace['clock'] = False
    dTrace['name'] = 'data_in'
    dTrace['direction'] = 'left'
    dReturn['traces'].append(dTrace)

    dTrace = {}
    dTrace['device_pin'] = 'O_DAC_DATA'
    dTrace['part_pin'] = 'SDIN'
    dTrace['clock'] = False
    dTrace['name'] = 'data_out'
    dTrace['direction'] = 'right'
    dReturn['traces'].append(dTrace)

    dTrace = {}
    dTrace['device_pin'] = 'O_DAC_SCLK'
    dTrace['part_pin'] = 'SCLK'
    dTrace['clock'] = True
    dTrace['name'] = 'clock'
    dTrace['direction'] = 'right'
    dReturn['traces'].append(dTrace)

    return dReturn


def render_text_diagram():
    lReturn = []

    lReturn.append('--------------+                    +------------')
    lReturn.append('   Arria10    |                    |  DAC81404  ')
    lReturn.append('              |                    |')
    lReturn.append('  I_DAC_DATA [ ]<--- data_in -----[ ] SDO')
    lReturn.append('              |                    |')
    lReturn.append('  O_DAC_DATA [ ]---- data_out --->[ ] SDIN')
    lReturn.append('              |                    |')
    lReturn.append('  O_DAC_SCLK [ ]----- clock ----->[ ] SCLK')
    lReturn.append('              |                    |')
    lReturn.append('--------------+                    +------------')

    return lReturn 
