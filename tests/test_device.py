
import unittest

from stacv import device


class Test(unittest.TestCase):


    def test_new_device(self):
 
        dDevice = create_device_dict()
        oDevice = device.new(dDevice)

        self.assertEqual('vendor_name', oDevice.vendor)
        self.assertEqual('device_name', oDevice.name)
        self.assertEqual(1, len(oDevice.interfaces))
        self.assertEqual('interface_name', oDevice.interfaces[0].name)


def create_device_dict():

    dDevice = {}
    
    dDevice['vendor'] = 'vendor_name'
    dDevice['name'] = 'device_name'
    
    dDevice['interface'] = []
    
    dInterface = {}
    dInterface['interface_name'] = {}

    dInterface['interface_name']['internal_clock'] = {}
    dInterface['interface_name']['internal_clock']['int_clock'] = {}
    dInterface['interface_name']['internal_clock']['int_clock']['frequency'] = '100 MHz'
    
    dInterface['interface_name']['external_clock'] = {}
    dInterface['interface_name']['external_clock']['clock_pin'] = {}
    dInterface['interface_name']['external_clock']['clock_pin']['frequency'] = '20 MHz'
    
    dInterface['interface_name']['data'] = []

    dPin = {}
    dPin['input_data_pin'] = {}
    dPin['input_data_pin']['capture_clock'] = 'int_clock'
    dPin['input_data_pin']['clock_edges'] = {}
    dPin['input_data_pin']['clock_edges']['from'] = 11
    dPin['input_data_pin']['clock_edges']['setup'] = 'c'
    dPin['input_data_pin']['clock_edges']['hold'] = 'd'
    dInterface['interface_name']['data'].append(dPin)

    dPin = {} 
    dPin['output_data_pin'] = {}
    dPin['output_data_pin']['launch_clock'] = 'int_clock'
    dPin['output_data_pin']['clock_edges'] = {}
    dPin['output_data_pin']['clock_edges']['from'] = 3 
    dPin['output_data_pin']['clock_edges']['setup'] = 'f'
    dPin['output_data_pin']['clock_edges']['hold'] = 'q'
    dInterface['interface_name']['data'].append(dPin)

    dDevice['interface'].append(dInterface)    
    
    return dDevice

