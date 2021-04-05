
import unittest

from stacv import part


def create_part_dict():

    dPart = {}
    
    dPart['vendor'] = 'vendor_name'
    dPart['name'] = 'part_name'
    
    dPart['interface'] = []
    
    dInterface = {}
    dInterface['interface_name'] = {}
    dInterface['interface_name']['timing_model'] = 'source_synchronous_with_round_trip'
    
    dInterface['interface_name']['clock'] = {}
    dInterface['interface_name']['clock']['clock_pin'] = {}
    dInterface['interface_name']['clock']['clock_pin']['max_freq'] = '20 MHz'
    
    dInterface['interface_name']['data'] = []

    dPin = {}
    dPin['input_data_pin'] = {}
    dPin['input_data_pin']['rising_edge'] = {}
    dPin['input_data_pin']['rising_edge']['setup'] = {}
    dPin['input_data_pin']['rising_edge']['setup']['id'] = 'tSDIS'
    dPin['input_data_pin']['rising_edge']['setup']['value'] = 5.0
    dPin['input_data_pin']['rising_edge']['hold'] = {}
    dPin['input_data_pin']['rising_edge']['hold']['id'] = 'tSDIH'
    dPin['input_data_pin']['rising_edge']['hold']['value'] = 1.0
    dInterface['interface_name']['data'].append(dPin)
 
    dPin = {}
    dPin['output_data_pin'] = {}
    dPin['output_data_pin']['falling_edge'] = {}
    dPin['output_data_pin']['falling_edge']['clock_to_out'] = {}
    dPin['output_data_pin']['falling_edge']['clock_to_out']['id'] = 'tSDODLY'
    dPin['output_data_pin']['falling_edge']['clock_to_out']['max'] = 10.5
    dPin['output_data_pin']['falling_edge']['clock_to_out']['min'] = 8.3
    dInterface['interface_name']['data'].append(dPin)

    dPart['interface'].append(dInterface)
 
    return dPart

dPart = create_part_dict()


class Test(unittest.TestCase):


    def test_new_part(self):
 
        oPart = part.new(dPart)

        self.assertEqual('vendor_name', oPart.vendor)
        self.assertEqual('part_name', oPart.name)
        self.assertEqual(1, len(oPart.interfaces))

    def test_get_interface_with_pin_named(self):

        oPart = part.new(dPart)

        oInterface = oPart.get_interface_with_pin_named('input_data_pin')

        self.assertEqual('interface_name', oInterface.name)

        self.assertEqual(None, oPart.get_interface_with_pin_named('nothing'))
