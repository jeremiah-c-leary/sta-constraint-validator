
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
    ############################################################################
    dInterface['interface_name']['clock'] = {}
    ############################################################################
    dInterface['interface_name']['clock']['internal'] = []
 
    dClock = {}
    dClock['internal_clock'] = {}
    dClock['internal_clock']['frequency'] = '100 MHz'

    dInterface['interface_name']['clock']['internal'].append(dClock)

    ############################################################################
    dInterface['interface_name']['clock']['output'] = []
 
    dClock = {}
    dClock['external_clock'] = {}
    dClock['external_clock']['frequency'] = '20 MHz'

    dInterface['interface_name']['clock']['output'].append(dClock)
    ############################################################################
    dInterface['interface_name']['clock']['input'] = []
 
    dClock = {}
    dClock['input_clock'] = {}
    dClock['input_clock']['frequency'] = '50 MHz'

    dInterface['interface_name']['clock']['input'].append(dClock)
    ############################################################################
    dInterface['interface_name']['data'] = {}
    ############################################################################
    dInterface['interface_name']['data']['output'] = []
    
    dPin = {} 
    dPin['output_data_pin'] = {}
    dPin['output_data_pin']['launch_clock'] = {}
    dPin['output_data_pin']['launch_clock']['name'] = 'internal_clock'
    dPin['output_data_pin']['launch_clock']['edge'] = 3

    dPin['output_data_pin']['capture_clock'] = {}
    dPin['output_data_pin']['capture_clock']['name'] = 'external_clock'
    dPin['output_data_pin']['capture_clock']['edge'] = {}
    dPin['output_data_pin']['capture_clock']['edge']['setup'] = 'f'
    dPin['output_data_pin']['capture_clock']['edge']['hold'] = 'q'

    dInterface['interface_name']['data']['output'].append(dPin)
    ############################################################################
    dInterface['interface_name']['data']['input'] = []

    dPin = {} 
    dPin['input_data_pin'] = {}
    dPin['input_data_pin']['launch_clock'] = {}
    dPin['input_data_pin']['launch_clock']['name'] = 'external_clock'
    dPin['input_data_pin']['launch_clock']['edge'] = 11

    dPin['input_data_pin']['capture_clock'] = {}
    dPin['input_data_pin']['capture_clock']['name'] = 'internal_clock'
    dPin['input_data_pin']['capture_clock']['edge'] = {}
    dPin['input_data_pin']['capture_clock']['edge']['setup'] = 'c'
    dPin['input_data_pin']['capture_clock']['edge']['hold'] = 'd'

    dInterface['interface_name']['data']['input'].append(dPin)
    ############################################################################

    dDevice['interface'].append(dInterface)    

    return dDevice
