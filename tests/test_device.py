
import unittest

from stacv import device


class Test(unittest.TestCase):


    def test_new_device(self):
 
        dDevice = create_device_dict()
        oPart = device.new(dDevice)

        self.assertEqual('vendor_name', oPart.vendor)
        self.assertEqual('device_name', oPart.name)
#        self.assertEqual(1, len(oPart.interfaces))


def create_device_dict():

    dDevice = {}
    
    dDevice['vendor'] = 'vendor_name'
    dDevice['name'] = 'device_name'
    
    dDevice['interface'] = {}
    
    dInterface = {}

    dInterface['internal_clock'] = {}
    dInterface['internal_clock']['int_clock'] = {}
    dInterface['internal_clock']['int_clock']['frequency'] = '100 MHz'
    
    dInterface['clock'] = {}
    dInterface['clock']['clock_pin'] = {}
    dInterface['clock']['clock_pin']['frequency'] = '20 MHz'
    
    dInterface['data'] = {}
    dInterface['data']['input_data_pin'] = {}
    dInterface['data']['input_data_pin']['capture_clock'] = 'int_clock'
    dInterface['data']['input_data_pin']['clock_edges'] = {}
    dInterface['data']['input_data_pin']['clock_edges']['from'] = 11
    dInterface['data']['input_data_pin']['clock_edges']['setup'] = 'c'
    dInterface['data']['input_data_pin']['clock_edges']['hold'] = 'd'
    
    dInterface['data']['output_data_pin'] = {}
    dInterface['data']['output_data_pin']['launch_clock'] = 'int_clock'
    dInterface['data']['output_data_pin']['clock_edges'] = {}
    dInterface['data']['output_data_pin']['clock_edges']['from'] = 3 
    dInterface['data']['output_data_pin']['clock_edges']['setup'] = 'f'
    dInterface['data']['output_data_pin']['clock_edges']['hold'] = 'q'
    
    dDevice['interface']['interface_name'] = dInterface
    
    return dDevice

