
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
        self.assertEqual(2, len(oInterface.clocks))
        self.assertTrue(isinstance(oInterface.clocks[0], pin.PartInputClockPin))
        self.assertTrue(isinstance(oInterface.clocks[1], pin.PartOutputClockPin))
        self.assertTrue(2, len(oInterface.data_pins))
        self.assertTrue(isinstance(oInterface.data_pins[0], pin.PartInputDataPin))
        self.assertTrue(isinstance(oInterface.data_pins[1], pin.PartOutputDataPin))


    def test_interface_has_pin_named(self):

        dInterface = create_part_dict()
        oInterface = interface.new(dInterface)

        self.assertTrue(oInterface.has_pin_named('input_data'))
        self.assertTrue(oInterface.has_pin_named('output_data'))
        self.assertTrue(oInterface.has_pin_named('clock_pin'))
        self.assertTrue(oInterface.has_pin_named('clock_pin_output'))
        self.assertFalse(oInterface.has_pin_named('nothing'))


def create_part_dict():

    dInterface = {}
    dInterface['name'] = 'interface_name'
    dInterface['location'] = 'part'
    dInterface['timing_model'] = 'source_synchronous_with_round_trip'
    
    dInterface['clock'] = {}
    dInterface['clock']['input'] = []

    dPin = {}
    dPin['clock_pin'] = {}
    dPin['clock_pin']['max_freq'] = '20 MHz'
    dInterface['clock']['input'].append(dPin)

    dInterface['clock']['output'] = []
    dPin = {}
    dPin['clock_pin_output'] = {}
    dPin['clock_pin_output']['max_freq'] = '20 MHz'
    dInterface['clock']['output'].append(dPin)

    dInterface['data'] = {}
    dInterface['data']['input'] = []

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

    dInterface['data']['input'].append(dPin)
    
    dInterface['data']['output'] = []

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

    dInterface['data']['output'].append(dPin)

    return dInterface


class TestDeviceInterface(unittest.TestCase):

    def test_new(self):
 
        dInterface = create_device_dict()
        oInterface = interface.new(dInterface)

        self.assertTrue(isinstance(oInterface, interface.DeviceInterface))
        self.assertEqual('interface_name', oInterface.name)

        self.assertEqual(1, len(oInterface.output_clocks))
        self.assertEqual('external_clock', oInterface.output_clocks[0].name)
        self.assertTrue(isinstance(oInterface.output_clocks[0], pin.DeviceOutputClockPin))

        self.assertEqual(1, len(oInterface.internal_clocks))
        self.assertEqual('internal_clock', oInterface.internal_clocks[0].name)
        self.assertTrue(isinstance(oInterface.internal_clocks[0], pin.DeviceInternalClock))


        self.assertEqual(2, len(oInterface.data_pins))

        self.assertTrue(isinstance(oInterface.data_pins[0], pin.DeviceOutputDataPin))
        self.assertEqual('output_data_pin', oInterface.data_pins[0].name)

        self.assertTrue(isinstance(oInterface.data_pins[1], pin.DeviceInputDataPin))
        self.assertEqual('input_data_pin', oInterface.data_pins[1].name)

def create_device_dict():

    dInterface = {}
    dInterface['name'] = 'interface_name'
    dInterface['location'] = 'device'
    ############################################################################
    dInterface['clock'] = {}
    ############################################################################
    dInterface['clock']['internal'] = []
 
    dClock = {}
    dClock['internal_clock'] = {}
    dClock['internal_clock']['frequency'] = '100 MHz'

    dInterface['clock']['internal'].append(dClock)

    ############################################################################
    dInterface['clock']['output'] = []
 
    dClock = {}
    dClock['external_clock'] = {}
    dClock['external_clock']['frequency'] = '20 MHz'

    dInterface['clock']['output'].append(dClock)
    ############################################################################
    dInterface['clock']['input'] = []
 
    dClock = {}
    dClock['input_clock'] = {}
    dClock['input_clock']['frequency'] = '50 MHz'

    dInterface['clock']['input'].append(dClock)
    ############################################################################
    dInterface['data'] = {}
    ############################################################################
    dInterface['data']['output'] = []
    
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

    dInterface['data']['output'].append(dPin)
    ############################################################################
    dInterface['data']['input'] = []

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

    dInterface['data']['input'].append(dPin)
    ############################################################################

    return dInterface

