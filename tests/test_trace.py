
import unittest

from stacv import trace


class Test(unittest.TestCase):

    def test_new_trace(self):
        sName = 'trace'
        sDevicePin = 'device_pin'
        sPartPin = 'part_pin'
        fMaxDelay = 1
        fMinDelay = 0.567

        oTrace = trace.New(sName, sDevicePin, sPartPin, fMaxDelay, fMinDelay)

        self.assertEqual(sName, oTrace.name)
        self.assertEqual(sDevicePin, oTrace.device_pin)
        self.assertEqual(sPartPin, oTrace.part_pin)
        self.assertEqual(fMaxDelay, oTrace.max_delay)
        self.assertEqual(fMinDelay, oTrace.min_delay)

    def test_min_delay_less_than_0(self):

        sName = 'trace'
        sDevicePin = 'device_pin'
        sPartPin = 'part_pin'
        fMaxDelay = 10
        fMinDelay = -1

        self.assertRaises(ValueError, trace.New, sName, sDevicePin, sPartPin, fMaxDelay, -1)

    def test_max_delay_less_than_min_delay(self):

        sName = 'trace'
        sDevicePin = 'device_pin'
        sPartPin = 'part_pin'

        self.assertRaises(ValueError, trace.New, sName, sDevicePin, sPartPin, 1, 2)
