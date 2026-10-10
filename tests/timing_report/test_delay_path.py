import unittest

from stacv.timing_report import delay_path
from stacv.timing_report import delay_element


def create_net_delay(sResource):
    oNetDelay = delay_element.NetDelay()
    oNetDelay.resource = sResource
    return oNetDelay


class Test(unittest.TestCase):

    def test_get_resources_of_empty_path(self):
        oDelayPath = delay_path.DelayPath('unknown')

        self.assertEqual([], oDelayPath.get_resources())

    def test_get_resources_in_path_order(self):
        oDelayPath = delay_path.DelayPath('unknown')
        oDelayPath.add_delay(create_net_delay('I_CLK'))
        oDelayPath.add_delay(create_net_delay('I_CLK_IBUF'))

        self.assertEqual(['I_CLK', 'I_CLK_IBUF'], oDelayPath.get_resources())
