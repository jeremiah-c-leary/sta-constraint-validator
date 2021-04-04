
import unittest

from stacv import part


def create_part_dict():

    dPart = {}
    
    dPart['vendor'] = 'vendor_name'
    dPart['name'] = 'part_name'
    
    dPart['interface'] = {}
    
    dInterface = {}
    dInterface['timing_model'] = 'source_synchronous_with_round_trip'
    
    dInterface['clock'] = {}
    dInterface['clock']['clock_pin'] = {}
    dInterface['clock']['clock_pin']['max_freq'] = '20 MHz'
    
    dInterface['data'] = {}
    dInterface['data']['input_data_pin'] = {}
    dInterface['data']['input_data_pin']['rising'] = {}
    dInterface['data']['input_data_pin']['rising']['setup'] = 5.0
    dInterface['data']['input_data_pin']['rising']['hold'] = 1.0
    
    dInterface['data']['output_data_pin'] = {}
    dInterface['data']['output_data_pin']['falling'] = {}
    dInterface['data']['output_data_pin']['falling']['clock_to_out'] = {}
    dInterface['data']['output_data_pin']['falling']['clock_to_out']['max'] = 10.5
    dInterface['data']['output_data_pin']['falling']['clock_to_out']['min'] = 8.3
    
    dPart['interface']['interface_name'] = dInterface
    
    return dPart

dPart = create_part_dict()


class Test(unittest.TestCase):


    def test_new_board(self):
 
        oPart = part.new(dPart)

        self.assertEqual('vendor_name', oPart.vendor)
        self.assertEqual('part_name', oPart.name)
        self.assertEqual(1, len(oPart.interfaces))

    def test_get_interface_with_pin_named(self):

        oPart = part.new(dPart)

        oInterface = oPart.get_interface_with_pin_named('input_data_pin')

        self.assertEqual('interface_name', oInterface.name)

        self.assertEqual(None, oPart.get_interface_with_pin_named('nothing'))
