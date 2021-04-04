
import unittest

from stacv import pin


class Test(unittest.TestCase):

    def test_new_clock_pin(self):
 
        dPin = create_clock_pin_dict()

        oPin = pin.new(dPin)

        self.assertEqual('clock_pin', oPin.name)
        self.assertEqual('20 MHz', oPin.max_freq)
        self.assertTrue(isinstance(oPin, pin.ClockPin))

    def test_new_input_data_pin(self):
 
        dInputDataPin = create_input_data_pin_dict()

        oPin = pin.new(dInputDataPin)

        self.assertEqual('input_pin', oPin.name)
        self.assertEqual(1.0, oPin.setup)
        self.assertEqual(0.5, oPin.hold)
        self.assertEqual('rising', oPin.edge)
        self.assertTrue(isinstance(oPin, pin.InputPin))

    def test_new_output_data_pin(self):
 
        dPin = create_output_data_pin_dict()

        oPin = pin.new(dPin)

        self.assertEqual('output_pin', oPin.name)
        self.assertEqual(5.0, oPin.cko_max)
        self.assertEqual(4.5, oPin.cko_min)
        self.assertEqual('rising', oPin.edge)
        self.assertTrue(isinstance(oPin, pin.OutputPin))


def create_clock_pin_dict():

    dPin = {}
    dPin['clock_pin'] = {}
    dPin['clock_pin']['max_freq'] = '20 MHz'
    
    return dPin



def create_input_data_pin_dict():
    dPin = {}
    dPin['input_pin'] = {}
    dPin['input_pin']['rising'] = {}
    dPin['input_pin']['rising']['setup'] = 1.0
    dPin['input_pin']['rising']['hold'] = 0.5

    return dPin

def create_output_data_pin_dict():
    dPin = {}
    dPin['output_pin'] = {}
    dPin['output_pin']['rising'] = {}
    dPin['output_pin']['rising']['clock_to_out'] = {}
    dPin['output_pin']['rising']['clock_to_out']['max'] = 5.0
    dPin['output_pin']['rising']['clock_to_out']['min'] = 4.5

    return dPin
