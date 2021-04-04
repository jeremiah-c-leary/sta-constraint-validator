
import unittest

from stacv import timing_model
from stacv import part
from stacv import board
from stacv import device
from stacv import interface


class Test(unittest.TestCase):

    def setUp(self):

        self.oPart = part.new(create_part_dict())
        self.oBoard = board.new(create_board_dict())
        self.oDevice = device.new(create_device_dict())


    def test_new_timing_model(self):

        oDeviceInterface = self.oDevice.get_interface_named('DAC_DATA') 
        oTM = timing_model.new(oDeviceInterface, self.oBoard, self.oPart)

        self.assertTrue(isinstance(oTM, timing_model.SourceSynchronousWithRoundTrip))
        self.assertTrue(isinstance(oTM.device_interface, interface.DeviceInterface))
        self.assertTrue(isinstance(oTM.part_interface, interface.PartInterface))
        self.assertEqual('serial_data', oTM.part_interface.name)
        self.assertTrue(isinstance(oTM.traces, board.Board))


def create_part_dict():

    dPart = {}
    
    dPart['vendor'] = 'Texas Instruments'
    dPart['name'] = 'DAC81404'
    
    dPart['interface'] = []
    
    dInterface = {}
    dInterface['serial_data'] = {}
    dInterface['serial_data']['timing_model'] = 'source_synchronous_with_round_trip'
    
    dInterface['serial_data']['clock'] = {}
    dInterface['serial_data']['clock']['SCLK'] = {}
    dInterface['serial_data']['clock']['SCLK']['max_freq'] = '50 MHz'
    
    dInterface['serial_data']['data'] = []

    dPin = {}
    dPin['SDIN'] = {}
    dPin['SDIN']['rising'] = {}
    dPin['SDIN']['rising']['setup'] = 5.0
    dPin['SDIN']['rising']['hold'] = 5.0
    dInterface['serial_data']['data'].append(dPin)
 
    dPin = {}
    dPin['SDO'] = {}
    dPin['SDO']['falling'] = {}
    dPin['SDO']['falling']['clock_to_out'] = {}
    dPin['SDO']['falling']['clock_to_out']['max'] = 20
    dPin['SDO']['falling']['clock_to_out']['min'] = 0
    dInterface['serial_data']['data'].append(dPin)

    dPart['interface'].append(dInterface)
 
    return dPart

def create_board_dict():

    dBoardConfig = {}
    dBoardConfig['board'] = {}
    dBoardConfig['board']['trace'] = []
    
    dTrace = {}
    dTrace['clock'] = {}
    dTrace['clock']['device_pin'] = 'O_DAC_SCLK'
    dTrace['clock']['part_pin'] = 'SCLK'
    dTrace['clock']['delay'] = {}
    dTrace['clock']['delay']['max'] = 2.0
    dTrace['clock']['delay']['min'] = 1.0
    
    dBoardConfig['board']['trace'].append(dTrace)
    
    dTrace = {}
    dTrace['data_out'] = {}
    dTrace['data_out']['device_pin'] = 'O_DAC_DATA'
    dTrace['data_out']['part_pin'] = 'SDIN'
    dTrace['data_out']['delay'] = {}
    dTrace['data_out']['delay']['max'] = 2.5
    dTrace['data_out']['delay']['min'] = 1.5
    
    dBoardConfig['board']['trace'].append(dTrace)
    
    dTrace = {}
    dTrace['data_in'] = {}
    dTrace['data_in']['device_pin'] = 'I_DAC_DATA'
    dTrace['data_in']['part_pin'] = 'SDO'
    dTrace['data_in']['delay'] = {}
    dTrace['data_in']['delay']['max'] = 1.5
    dTrace['data_in']['delay']['min'] = 0.5
    
    dBoardConfig['board']['trace'].append(dTrace)

    return dBoardConfig


def create_device_dict():

    dDevice = {}
    
    dDevice['vendor'] = 'Intel'
    dDevice['name'] = 'Arria10'
    
    dDevice['interface'] = []
    
    dInterface = {}
    dInterface['DAC_DATA'] = {}

    dInterface['DAC_DATA']['internal_clock'] = {}
    dInterface['DAC_DATA']['internal_clock']['int_clock'] = {}
    dInterface['DAC_DATA']['internal_clock']['int_clock']['frequency'] = '100 MHz'
    
    dInterface['DAC_DATA']['external_clock'] = {}
    dInterface['DAC_DATA']['external_clock']['O_DAC_SCLK'] = {}
    dInterface['DAC_DATA']['external_clock']['O_DAC_SCLK']['frequency'] = '20 MHz'
    
    dInterface['DAC_DATA']['data'] = []

    dPin = {}
    dPin['I_DAC_DATA'] = {}
    dPin['I_DAC_DATA']['capture_clock'] = 'int_clock'
    dPin['I_DAC_DATA']['clock_edges'] = {}
    dPin['I_DAC_DATA']['clock_edges']['from'] = 11
    dPin['I_DAC_DATA']['clock_edges']['setup'] = 'c'
    dPin['I_DAC_DATA']['clock_edges']['hold'] = 'd'
    dInterface['DAC_DATA']['data'].append(dPin)

    dPin = {} 
    dPin['O_DAC_DATA'] = {}
    dPin['O_DAC_DATA']['launch_clock'] = 'int_clock'
    dPin['O_DAC_DATA']['clock_edges'] = {}
    dPin['O_DAC_DATA']['clock_edges']['from'] = 3 
    dPin['O_DAC_DATA']['clock_edges']['setup'] = 'f'
    dPin['O_DAC_DATA']['clock_edges']['hold'] = 'q'
    dInterface['DAC_DATA']['data'].append(dPin)

    dDevice['interface'].append(dInterface)    
    
    return dDevice

