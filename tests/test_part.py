
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
    dInterface['interface_name']['clock']['input'] = []

    dPin = {}
    dPin['clock_pin'] = {}
    dPin['clock_pin']['max_freq'] = '20 MHz'
    dInterface['interface_name']['clock']['input'].append(dPin)

    dInterface['interface_name']['clock']['output'] = []
    dPin = {}
    dPin['clock_pin_output'] = {}
    dPin['clock_pin_output']['max_freq'] = '20 MHz'
    dInterface['interface_name']['clock']['output'].append(dPin)

    dInterface['interface_name']['data'] = {}
    dInterface['interface_name']['data']['input'] = []

    dPin = {}
    dPin['input_data'] = {}
    dPin['input_data']['clock'] = 'clock_pin'
    dPin['input_data']['rising'] = {}
    dPin['input_data']['rising']['setup'] = {}
    dPin['input_data']['rising']['setup']['id'] = 'rising_setup_id'
    dPin['input_data']['rising']['setup']['value'] = 5.0
    dPin['input_data']['rising']['hold'] = {}
    dPin['input_data']['rising']['hold']['id'] = 'rising_hold_id'
    dPin['input_data']['rising']['hold']['value'] = 1.0
    dPin['input_data']['falling'] = {}
    dPin['input_data']['falling']['setup'] = {}
    dPin['input_data']['falling']['setup']['id'] = 'falling_setup_id'
    dPin['input_data']['falling']['setup']['value'] = 15.0
    dPin['input_data']['falling']['hold'] = {}
    dPin['input_data']['falling']['hold']['id'] = 'falling_hold_id'
    dPin['input_data']['falling']['hold']['value'] = 1.0

    dInterface['interface_name']['data']['input'].append(dPin)
    
    dInterface['interface_name']['data']['output'] = []

    dPin = {}
    dPin['output_data'] = {}
    dPin['output_data']['clock'] = 'clock_pin_output'
    dPin['output_data']['rising'] = {}
    dPin['output_data']['rising']['clock_to_out_max'] = {}
    dPin['output_data']['rising']['clock_to_out_max']['id'] = 'rising_cko_max_id'
    dPin['output_data']['rising']['clock_to_out_max']['value'] = 7.0
    dPin['output_data']['rising']['clock_to_out_min'] = {}
    dPin['output_data']['rising']['clock_to_out_min']['id'] = 'rising_cko_min_id'
    dPin['output_data']['rising']['clock_to_out_min']['value'] = 2.0
    dPin['output_data']['falling'] = {}
    dPin['output_data']['falling']['clock_to_out_max'] = {}
    dPin['output_data']['falling']['clock_to_out_max']['id'] = 'falling_cko_max_id'
    dPin['output_data']['falling']['clock_to_out_max']['value'] = 17.0
    dPin['output_data']['falling']['clock_to_out_min'] = {}
    dPin['output_data']['falling']['clock_to_out_min']['id'] = 'falling_cko_min_id'
    dPin['output_data']['falling']['clock_to_out_min']['value'] = 12.0

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

        oInterface = oPart.get_interface_with_pin_named('input_data')

        self.assertEqual('interface_name', oInterface.name)

        self.assertEqual(None, oPart.get_interface_with_pin_named('nothing'))
