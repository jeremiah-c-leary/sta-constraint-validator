
import unittest

from stacv import interface
from stacv import pin


class TestPartInterface(unittest.TestCase):

    def test_new(self):
 
        dInterface = create_part_dict()
        oInterface = interface.new(dInterface)

        self.assertTrue(isinstance(oInterface, interface.PartInterface))
        self.assertEqual('interface_name', oInterface.name)
        self.assertEqual('source_synchronous_with_round_trip', oInterface.timing_model)
        self.assertEqual('clock_pin', oInterface.clock_pin.name)
        self.assertTrue(isinstance(oInterface.clock_pin, pin.ClockPin))
        self.assertEqual(2, len(oInterface.data_pins))

    def test_interface_has_pin_named(self):

        dInterface = create_part_dict()
        oInterface = interface.new(dInterface)

        self.assertTrue(oInterface.has_pin_named('input_data_pin'))
        self.assertTrue(oInterface.has_pin_named('output_data_pin'))
        self.assertTrue(oInterface.has_pin_named('clock_pin'))
        self.assertFalse(oInterface.has_pin_named('nothing'))


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


class TestDeviceInterface(unittest.TestCase):

    def test_new(self):
 
        dInterface = create_device_dict()
        oInterface = interface.new(dInterface)

        self.assertTrue(isinstance(oInterface, interface.DeviceInterface))
        self.assertEqual('interface_name', oInterface.name)
        self.assertEqual('clock_pin', oInterface.external_clock.name)
        self.assertTrue(isinstance(oInterface.external_clock, pin.ClockPin))
        self.assertEqual('int_clock', oInterface.internal_clock.name)
        self.assertTrue(isinstance(oInterface.internal_clock, pin.ClockPin))
        self.assertEqual(2, len(oInterface.data_pins))
        self.assertTrue(isinstance(oInterface.data_pins[0], pin.DeviceInputPin))
        self.assertEqual('input_data_pin', oInterface.data_pins[0].name)
        self.assertTrue(isinstance(oInterface.data_pins[1], pin.DeviceOutputPin))
        self.assertEqual('output_data_pin', oInterface.data_pins[1].name)

def create_device_dict():

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

    return dInterface

