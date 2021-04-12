
import unittest

from stacv.timing_report import delay_element
from stacv.timing_report import delay_path


class Test(unittest.TestCase):

    def test_new_part_output_clock_pin(self):

        oDelayPath = delay_path.new()

        oDelay = create_delay_object('K12')
        oDelayPath.add_delay(oDelay)

        self.assertEqual(1, len(oDelayPath.delays))

        oDelay = create_delay_object('K14')
        oDelayPath.add_delay(oDelay)

        self.assertEqual(2, len(oDelayPath.delays))

        self.assertEqual('K12', oDelayPath.delays[0].location)
        self.assertEqual('K14', oDelayPath.delays[1].location)
        self.assertTrue(isinstance(oDelayPath, delay_path.DelayPath))


def create_delay_object(location):

    dDelay = {}
    dDelay['type'] = 'cell'
    dDelay['location'] = location
    dDelay['delay_type'] = 'net'
    dDelay['delay'] = 0
    dDelay['resource'] = 'I_CLK'
  
    oDelay = delay_element.new(dDelay)

    return oDelay
