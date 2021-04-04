
import unittest

from stacv import interface
from stacv import pin


def create_part_dict():

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
    
    return dInterface

dInterface = create_part_dict()


class Test(unittest.TestCase):

    def test_new(self):
 
        oInterface = interface.new('interface_name', dInterface)

        self.assertEqual('interface_name', oInterface.name)
        self.assertEqual('source_synchronous_with_round_trip', oInterface.timing_model)
        self.assertEqual('clock_pin', oInterface.clock_pin.name)
        self.assertTrue(isinstance(oInterface.clock_pin, pin.ClockPin))
        self.assertEqual(2, len(oInterface.data_pins))

    def test_has_pin_named(self):

        oInterface = interface.new('interface_name', dInterface)

        self.assertTrue(oInterface.has_pin_named('input_data_pin'))
        self.assertTrue(oInterface.has_pin_named('output_data_pin'))
        self.assertTrue(oInterface.has_pin_named('clock_pin'))
        self.assertFalse(oInterface.has_pin_named('nothing'))
