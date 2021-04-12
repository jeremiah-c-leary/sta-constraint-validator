
import unittest

from stacv.timing_report import delay_element


class Test(unittest.TestCase):

    def test_new_part_output_clock_pin(self):
 
        dDelay = create_part_output_clock_pin_dict()

        oDelay = delay_element.new(dDelay)

        self.assertEqual('K18', oDelay.location)
        self.assertEqual('net', oDelay.delay_type)
        self.assertEqual(0, oDelay.delay)
        self.assertEqual('I_CLK', oDelay.resource)
        self.assertTrue(isinstance(oDelay, delay_element.CellDelay))


def create_part_output_clock_pin_dict():

    dDelay = {}
    dDelay['type'] = 'cell'
    dDelay['location'] = 'K18'
    dDelay['delay_type'] = 'net'
    dDelay['delay'] = 0
    dDelay['resource'] = 'I_CLK'
    
    return dDelay
