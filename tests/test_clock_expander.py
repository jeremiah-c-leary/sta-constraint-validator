
import unittest

from stacv import clock


class Test(unittest.TestCase):

    def test_expand_20_mhz_clock(self):
 
        oClock = clock.new('20 MHz')
        clock.expand(oClock, 2)

        self.assertTrue(isinstance(oClock, clock.clock))
        self.assertEqual('20 MHz', oClock.freq)
        self.assertEqual(50, oClock.period)

        self.assertEqual(5, len(oClock.edges))

        self.assertTrue(isinstance(oClock.edges[0], clock.edge))
        self.assertTrue(isinstance(oClock.edges[1], clock.edge))
        self.assertTrue(isinstance(oClock.edges[2], clock.edge))
        self.assertTrue(isinstance(oClock.edges[3], clock.edge))
        self.assertTrue(isinstance(oClock.edges[4], clock.edge))

        self.assertEqual(1, oClock.edges[0].id)
        self.assertEqual(2, oClock.edges[1].id)
        self.assertEqual(3, oClock.edges[2].id)
        self.assertEqual(4, oClock.edges[3].id)
        self.assertEqual(5, oClock.edges[4].id)

        self.assertEqual('rising', oClock.edges[0].direction)
        self.assertEqual('falling', oClock.edges[1].direction)
        self.assertEqual('rising', oClock.edges[2].direction)
        self.assertEqual('falling', oClock.edges[3].direction)
        self.assertEqual('rising', oClock.edges[4].direction)

        self.assertEqual(0, oClock.edges[0].time)
        self.assertEqual(25, oClock.edges[1].time)
        self.assertEqual(50, oClock.edges[2].time)
        self.assertEqual(75, oClock.edges[3].time)
        self.assertEqual(100, oClock.edges[4].time)

    def test_expand_100_mhz_clock(self):
 
        oClock = clock.new('100 MHz')
        clock.expand(oClock, 3)

        self.assertTrue(isinstance(oClock, clock.clock))

        self.assertEqual('100 MHz', oClock.freq)
        self.assertEqual(10, oClock.period)

        self.assertEqual(7, len(oClock.edges))

        self.assertTrue(isinstance(oClock.edges[0], clock.edge))
        self.assertTrue(isinstance(oClock.edges[1], clock.edge))
        self.assertTrue(isinstance(oClock.edges[2], clock.edge))
        self.assertTrue(isinstance(oClock.edges[3], clock.edge))
        self.assertTrue(isinstance(oClock.edges[4], clock.edge))
        self.assertTrue(isinstance(oClock.edges[5], clock.edge))
        self.assertTrue(isinstance(oClock.edges[6], clock.edge))

        self.assertEqual(1, oClock.edges[0].id)
        self.assertEqual(2, oClock.edges[1].id)
        self.assertEqual(3, oClock.edges[2].id)
        self.assertEqual(4, oClock.edges[3].id)
        self.assertEqual(5, oClock.edges[4].id)
        self.assertEqual(6, oClock.edges[5].id)
        self.assertEqual(7, oClock.edges[6].id)

        self.assertEqual('rising', oClock.edges[0].direction)
        self.assertEqual('falling', oClock.edges[1].direction)
        self.assertEqual('rising', oClock.edges[2].direction)
        self.assertEqual('falling', oClock.edges[3].direction)
        self.assertEqual('rising', oClock.edges[4].direction)
        self.assertEqual('falling', oClock.edges[5].direction)
        self.assertEqual('rising', oClock.edges[6].direction)

        self.assertEqual(0, oClock.edges[0].time)
        self.assertEqual(5, oClock.edges[1].time)
        self.assertEqual(10, oClock.edges[2].time)
        self.assertEqual(15, oClock.edges[3].time)
        self.assertEqual(20, oClock.edges[4].time)
        self.assertEqual(25, oClock.edges[5].time)
        self.assertEqual(30, oClock.edges[6].time)

    def test_expand_1_khz_clock(self):
 
        oClock = clock.new('1 kHz')
        clock.expand(oClock, 2)

        self.assertTrue(isinstance(oClock, clock.clock))
        self.assertEqual('1 kHz', oClock.freq)
        self.assertEqual(1000000, oClock.period)

        self.assertEqual(5, len(oClock.edges))

        self.assertTrue(isinstance(oClock.edges[0], clock.edge))
        self.assertTrue(isinstance(oClock.edges[1], clock.edge))
        self.assertTrue(isinstance(oClock.edges[2], clock.edge))
        self.assertTrue(isinstance(oClock.edges[3], clock.edge))
        self.assertTrue(isinstance(oClock.edges[4], clock.edge))

        self.assertEqual(1, oClock.edges[0].id)
        self.assertEqual(2, oClock.edges[1].id)
        self.assertEqual(3, oClock.edges[2].id)
        self.assertEqual(4, oClock.edges[3].id)
        self.assertEqual(5, oClock.edges[4].id)

        self.assertEqual('rising', oClock.edges[0].direction)
        self.assertEqual('falling', oClock.edges[1].direction)
        self.assertEqual('rising', oClock.edges[2].direction)
        self.assertEqual('falling', oClock.edges[3].direction)
        self.assertEqual('rising', oClock.edges[4].direction)

        self.assertEqual(0, oClock.edges[0].time)
        self.assertEqual(500000, oClock.edges[1].time)
        self.assertEqual(1000000, oClock.edges[2].time)
        self.assertEqual(1500000, oClock.edges[3].time)
        self.assertEqual(2000000, oClock.edges[4].time)

