import os
import unittest

from stacv.analysis import report_view

sReportDir = os.path.join(os.path.dirname(__file__), '..', 'timing_report', 'parse', 'vivado')


def load(sName):
    with open(os.path.join(sReportDir, sName)) as oFile:
        return report_view.parse(oFile.readlines(), sName)


class TestSetupReport(unittest.TestCase):

    def setUp(self):
        self.paths = load('dac_spi.setup.rpt')
        self.path = self.paths[0]

    def test_one_path_found(self):
        self.assertEqual(1, len(self.paths))

    def test_header(self):
        self.assertEqual('q_spi_output_data_reg/C', self.path.source)
        self.assertEqual('O_DAC_DATA', self.path.destination)
        self.assertEqual('setup', self.path.check)
        self.assertEqual('Fast Process Corner', self.path.corner)
        self.assertEqual(7.192, self.path.slack)
        self.assertTrue(self.path.met)

    def test_clocks(self):
        self.assertEqual('clk_100mhz', self.path.launch_clock.name)
        self.assertEqual(10.0, self.path.launch_clock.period)
        self.assertEqual('dac_sclk', self.path.capture_clock.name)
        self.assertEqual(25.0, self.path.capture_clock.fall)

    def test_edges_and_totals(self):
        self.assertEqual(40.0, self.path.launch_edge)
        self.assertEqual(50.0, self.path.capture_edge)
        self.assertEqual(43.984, self.path.arrival)
        self.assertEqual(51.176, self.path.required)

    def test_sections(self):
        self.assertEqual(41.924, self.path.source_clock_rows[-1].path)
        self.assertEqual('FDCE (Prop_fdce_C_Q)', self.path.data_rows[0].description)
        self.assertEqual(['clock pessimism', 'clock uncertainty', 'output delay'],
                         [r.description for r in self.path.capture_rows if r.kind == 'adjust'])

    def test_net_fanout(self):
        self.assertEqual(13, self.path.source_clock_rows[-1].fanout)

    def test_slack_matches_rows(self):
        self.assertAlmostEqual(self.path.slack, self.path.required - self.path.arrival, places=3)


class TestHoldReport(unittest.TestCase):

    def setUp(self):
        self.path = load('dac_spi.hold.rpt')[0]

    def test_hold_required_time_is_positive(self):
        self.assertEqual('hold', self.path.check)
        self.assertEqual(2.714, self.path.required)
        self.assertEqual(2.986, self.path.arrival)

    def test_slack_matches_rows(self):
        self.assertAlmostEqual(self.path.slack, self.path.arrival - self.path.required, places=3)


class TestCombinedReport(unittest.TestCase):

    def test_two_paths(self):
        lLines = []
        for sName in ('dac_spi.setup.rpt', 'dac_spi.hold.rpt'):
            with open(os.path.join(sReportDir, sName)) as oFile:
                lLines.extend(oFile.readlines())
        lPaths = report_view.parse(lLines)
        self.assertEqual(['setup', 'hold'], [p.check for p in lPaths])


class TestClock(unittest.TestCase):

    def test_levels(self):
        oClock = report_view.Clock('clk', 0.0, 5.0, 10.0)
        self.assertEqual(1, oClock.level_at(1.0))
        self.assertEqual(0, oClock.level_at(6.0))
        self.assertEqual(1, oClock.level_at(41.0))


class TestEmptyReport(unittest.TestCase):

    def test_empty_report(self):
        self.assertEqual([], report_view.parse(['nothing here']))

