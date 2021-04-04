
import unittest

from stacv import interface
from stacv import pin


def create_part_dict():

    dInterface = {}
    dInterface['interface_name'] = {}
    dInterface['interface_name']['timing_model'] = 'source_synchronous_with_round_trip'
    
    dInterface['interface_name']['clock'] = {}
    dInterface['interface_name']['clock']['clock_pin'] = {}
    dInterface['interface_name']['clock']['clock_pin']['max_freq'] = '20 MHz'
    
    dInterface['interface_name']['data'] = []
    dPin = {}
    dPin['input_data_pin'] = {}
    dPin['input_data_pin']['rising'] = {}
    dPin['input_data_pin']['rising']['setup'] = 5.0
    dPin['input_data_pin']['rising']['hold'] = 1.0
    dInterface['interface_name']['data'].append(dPin)

    dPin = {}
    dPin['output_data_pin'] = {}
    dPin['output_data_pin']['falling'] = {}
    dPin['output_data_pin']['falling']['clock_to_out'] = {}
    dPin['output_data_pin']['falling']['clock_to_out']['max'] = 10.5
    dPin['output_data_pin']['falling']['clock_to_out']['min'] = 8.3
    dInterface['interface_name']['data'].append(dPin)
    
    return dInterface

dInterface = create_part_dict()


class Test(unittest.TestCase):

    def test_new(self):
 
        oInterface = interface.new(dInterface)

        self.assertEqual('interface_name', oInterface.name)
        self.assertEqual('source_synchronous_with_round_trip', oInterface.timing_model)
        self.assertEqual('clock_pin', oInterface.clock_pin.name)
        self.assertTrue(isinstance(oInterface.clock_pin, pin.ClockPin))
        self.assertEqual(2, len(oInterface.data_pins))

    def test_has_pin_named(self):

        oInterface = interface.new(dInterface)

        self.assertTrue(oInterface.has_pin_named('input_data_pin'))
        self.assertTrue(oInterface.has_pin_named('output_data_pin'))
        self.assertTrue(oInterface.has_pin_named('clock_pin'))
        self.assertFalse(oInterface.has_pin_named('nothing'))
