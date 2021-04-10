
import unittest

from stacv import pin


class Test(unittest.TestCase):

    def test_new_part_output_clock_pin(self):
 
        dPin = create_part_output_clock_pin_dict()

        oPin = pin.new(dPin)

        self.assertEqual('clock_pin_out', oPin.name)
        self.assertEqual('10 MHz', oPin.max_freq)
        self.assertTrue(isinstance(oPin, pin.PartOutputClockPin))

    def test_new_part_input_clock_pin(self):
 
        dPin = create_part_input_clock_pin_dict()

        oPin = pin.new(dPin)

        self.assertEqual('clock_pin', oPin.name)
        self.assertEqual('20 MHz', oPin.max_freq)
        self.assertTrue(isinstance(oPin, pin.PartInputClockPin))

    def test_new_part_input_data_pin(self):
 
        dPin = create_part_input_data_pin_dict()

        oPin = pin.new(dPin)

        self.assertEqual('input_data', oPin.name)
        self.assertEqual(1.0, oPin.rising_edge_setup)
        self.assertEqual(0.5, oPin.rising_edge_hold)
        self.assertEqual(2.0, oPin.falling_edge_setup)
        self.assertEqual(2.5, oPin.falling_edge_hold)
        self.assertTrue(isinstance(oPin, pin.PartInputDataPin))

    def test_new_part_output_data_pin(self):
 
        dPin = create_part_output_data_pin_dict()

        oPin = pin.new(dPin)

        self.assertEqual('output_data', oPin.name)
        self.assertEqual('tCKOMax', oPin.rising_cko_max_id)
        self.assertEqual(2.0, oPin.rising_cko_max)
        self.assertEqual('tCKOMin', oPin.rising_cko_min_id)
        self.assertEqual(1.0, oPin.rising_cko_min)
        self.assertEqual('tCKOMax_falling', oPin.falling_cko_max_id)
        self.assertEqual(5.0, oPin.falling_cko_max)
        self.assertEqual('tCKOMin_falling', oPin.falling_cko_min_id)
        self.assertEqual(1.5, oPin.falling_cko_min)
        self.assertTrue(isinstance(oPin, pin.PartOutputDataPin))

    def test_new_device_output_data_pin(self):
 
        dPin = create_device_output_data_pin_dict()

        oPin = pin.new(dPin)

        self.assertEqual('output_pin', oPin.name)
        self.assertEqual('internal_clock', oPin.launch_clock)
        self.assertEqual(3, oPin.launch_edge)
        self.assertEqual('output_clock', oPin.capture_clock)
        self.assertEqual('g', oPin.setup_edge)
        self.assertEqual('a', oPin.hold_edge)
        self.assertEqual('output', oPin.direction)
        self.assertTrue(isinstance(oPin, pin.DeviceOutputDataPin))

    def test_new_device_input_data_pin(self):
 
        dPin = create_device_input_data_pin_dict()

        oPin = pin.new(dPin)

        self.assertEqual('input_pin', oPin.name)
        self.assertEqual('output_clock', oPin.launch_clock)
        self.assertEqual(10, oPin.launch_edge)
        self.assertEqual('internal_clock', oPin.capture_clock)
        self.assertEqual('r', oPin.setup_edge)
        self.assertEqual('t', oPin.hold_edge)
        self.assertEqual('input', oPin.direction)
        self.assertTrue(isinstance(oPin, pin.DeviceInputDataPin))

    def test_new_device_output_clock_pin(self):

        dPin = create_device_output_clock_pin_dict()

        oPin = pin.new(dPin)

        self.assertEqual('output_clock', oPin.name)
        self.assertEqual('100 MHz', oPin.frequency)
        self.assertEqual('output', oPin.direction)
        self.assertTrue(isinstance(oPin, pin.DeviceOutputClockPin))

    def test_new_device_input_clock_pin(self):

        dPin = create_device_input_clock_pin_dict()

        oPin = pin.new(dPin)

        self.assertEqual('input_clock', oPin.name)
        self.assertEqual('50 MHz', oPin.frequency)
        self.assertEqual('input', oPin.direction)
        self.assertTrue(isinstance(oPin, pin.DeviceInputClockPin))

    def test_new_device_internal_clock(self):

        dPin = create_device_internal_clock_dict()

        oPin = pin.new(dPin)

        self.assertEqual('internal_clock', oPin.name)
        self.assertEqual('25 MHz', oPin.frequency)
        self.assertTrue(isinstance(oPin, pin.DeviceInternalClock))


def create_part_output_clock_pin_dict():

    dPin = {}
    dPin['name'] = 'clock_pin_out'
    dPin['pin_type'] = 'clock'
    dPin['location'] = 'part'
    dPin['direction'] = 'output'
    dPin['max_freq'] = '10 MHz'
    
    return dPin


def create_part_input_clock_pin_dict():

    dPin = {}
    dPin['name'] = 'clock_pin'
    dPin['pin_type'] = 'clock'
    dPin['location'] = 'part'
    dPin['direction'] = 'input'
    dPin['max_freq'] = '20 MHz'
    
    return dPin


def create_part_input_data_pin_dict():
    dPin = {}
    dPin['name'] = 'input_data'
    dPin['pin_type'] = 'data'
    dPin['location'] = 'part'
    dPin['direction'] = 'input'
    dPin['rising'] = {}
    dPin['rising']['setup'] = 1.0
    dPin['rising']['hold'] = 0.5
    dPin['falling'] = {}
    dPin['falling']['setup'] = 2.0
    dPin['falling']['hold'] = 2.5

    return dPin

def create_part_output_data_pin_dict():
    dPin = {}
    dPin['name'] = 'output_data'
    dPin['pin_type'] = 'data'
    dPin['location'] = 'part'
    dPin['direction'] = 'output'
    dPin['rising'] = {}
    dPin['rising']['max'] = {}
    dPin['rising']['max']['id'] = 'tCKOMax'
    dPin['rising']['max']['value'] = 2.0
    dPin['rising']['min'] = {}
    dPin['rising']['min']['id'] = 'tCKOMin'
    dPin['rising']['min']['value'] = 1.0
    dPin['falling'] = {}
    dPin['falling']['max'] = {}
    dPin['falling']['max']['id'] = 'tCKOMax_falling'
    dPin['falling']['max']['value'] = 5.0
    dPin['falling']['min'] = {}
    dPin['falling']['min']['id'] = 'tCKOMin_falling'
    dPin['falling']['min']['value'] = 1.5

    return dPin

def create_device_input_clock_pin_dict():
    dPin = {}
    dPin['name'] = 'input_clock'
    dPin['pin_type'] = 'clock'
    dPin['location'] = 'device'
    dPin['direction'] = 'input'
    dPin['frequency'] = '50 MHz'

    return dPin

def create_device_internal_clock_dict():
    dPin = {}
    dPin['name'] = 'internal_clock'
    dPin['pin_type'] = 'clock'
    dPin['location'] = 'device'
    dPin['direction'] = 'internal'
    dPin['frequency'] = '25 MHz'

    return dPin

def create_device_output_clock_pin_dict():
    dPin = {}
    dPin['name'] = 'output_clock'
    dPin['pin_type'] = 'clock'
    dPin['location'] = 'device'
    dPin['direction'] = 'output'
    dPin['frequency'] = '100 MHz'

    return dPin


def create_device_output_data_pin_dict():
    dPin = {}
    dPin['name'] = 'output_pin'
    dPin['pin_type'] = 'data'
    dPin['location'] = 'device'
    dPin['direction'] = 'output'
    dPin['launch_clock'] = {}
    dPin['launch_clock']['name'] = 'internal_clock'
    dPin['launch_clock']['edge'] = 3

    dPin['capture_clock'] = {}
    dPin['capture_clock']['name'] = 'output_clock'
    dPin['capture_clock']['edge'] = {}
    dPin['capture_clock']['edge']['setup'] = 'g'
    dPin['capture_clock']['edge']['hold'] = 'a'

    return dPin


def create_device_input_data_pin_dict():
    dPin = {}
    dPin['name'] = 'input_pin'
    dPin['pin_type'] = 'data'
    dPin['location'] = 'device'
    dPin['direction'] = 'input'
    dPin['launch_clock'] = {}
    dPin['launch_clock']['name'] = 'output_clock'
    dPin['launch_clock']['edge'] = 10

    dPin['capture_clock'] = {}
    dPin['capture_clock']['name'] = 'internal_clock'
    dPin['capture_clock']['edge'] = {}
    dPin['capture_clock']['edge']['setup'] = 'r'
    dPin['capture_clock']['edge']['hold'] = 't'

    return dPin
