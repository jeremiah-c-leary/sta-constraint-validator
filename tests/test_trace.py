
import unittest

from stacv import trace


class Test(unittest.TestCase):

    def test_new_trace(self):
        sName = 'trace'
        sDevicePin = 'device_pin'
        sPartPin = 'part_pin'
        fMaxDelay = 1
        fMinDelay = 0.567

        dTrace = {}
        dTrace[sName] = {}
        dTrace[sName]['device_pin'] = sDevicePin
        dTrace[sName]['part_pin'] = sPartPin
        dTrace[sName]['delay'] = {}
        dTrace[sName]['delay']['max'] = fMaxDelay
        dTrace[sName]['delay']['min'] = fMinDelay

        oTrace = trace.New(dTrace)

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

        dTrace = {}
        dTrace[sName] = {}
        dTrace[sName]['device_pin'] = sDevicePin
        dTrace[sName]['part_pin'] = sPartPin
        dTrace[sName]['delay'] = {}
        dTrace[sName]['delay']['max'] = fMaxDelay
        dTrace[sName]['delay']['min'] = fMinDelay

        self.assertRaises(ValueError, trace.New, dTrace)

    def test_max_delay_less_than_min_delay(self):

        sName = 'trace'
        sDevicePin = 'device_pin'
        sPartPin = 'part_pin'
        fMaxDelay = 2
        fMinDelay = 3

        dTrace = {}
        dTrace[sName] = {}
        dTrace[sName]['device_pin'] = sDevicePin
        dTrace[sName]['part_pin'] = sPartPin
        dTrace[sName]['delay'] = {}
        dTrace[sName]['delay']['max'] = fMaxDelay
        dTrace[sName]['delay']['min'] = fMinDelay

        self.assertRaises(ValueError, trace.New, dTrace)
