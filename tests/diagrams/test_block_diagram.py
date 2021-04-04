
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


    def test_new_timing_model(self):
        self.maxDiff = None
        oDeviceInterface = self.oDevice.get_interface_named('DAC_DATA') 
        oTM = timing_model.new(oDeviceInterface, self.oBoard, self.oPart)

        dExpected = generate_block_diagram_dictionary()

        self.assertEqual(dExpected, block_diagram.extract_data_structure(oTM))


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
