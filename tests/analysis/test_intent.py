import os
import unittest

from stacv import utils
from stacv.analysis import intent, report_view

sRoot = os.path.join(os.path.dirname(__file__), '..', '..')
sReportDir = os.path.join(sRoot, 'tests', 'timing_report', 'parse', 'vivado')


def load(sName):
    with open(os.path.join(sReportDir, sName)) as oFile:
        return report_view.parse(oFile.readlines(), sName)[0]


class TestEdgeNumbering(unittest.TestCase):

    def setUp(self):
        self.fast = report_view.Clock('fast', 0.0, 5.0, 10.0)
        self.slow = report_view.Clock('slow', 0.0, 25.0, 50.0)

    def test_numbered_edges(self):
        self.assertEqual(0.0, intent.edge_time(self.fast, 1))
        self.assertEqual(5.0, intent.edge_time(self.fast, 2))
        self.assertEqual(25.0, intent.edge_time(self.fast, 6))
        self.assertEqual(40.0, intent.edge_time(self.fast, 9))

    def test_lettered_edges(self):
        self.assertEqual(0.0, intent.edge_time(self.slow, intent.letter_to_index('a')))
        self.assertEqual(25.0, intent.edge_time(self.slow, intent.letter_to_index('b')))
        self.assertEqual(50.0, intent.edge_time(self.slow, intent.letter_to_index('c')))

    def test_edge_names(self):
        self.assertEqual('edge 9', intent.edge_name(self.fast, 40.0, True))
        self.assertEqual('c', intent.edge_name(self.slow, 50.0, False))
        self.assertEqual('30.000 ns (no edge)', intent.edge_name(self.slow, 30.0, False))

    def test_common_period(self):
        self.assertEqual(50.0, intent.common_period(self.fast, self.slow))


class TestSpiComparison(unittest.TestCase):

    def setUp(self):
        dConfig = utils.read_config_file(os.path.join(sRoot, 'tests', 'analysis', 'config_edge6.yaml'))
        self.comparison = intent.compare(dConfig, load('dac_spi.setup.rpt'), load('dac_spi.hold.rpt'))

    def test_intended_edges(self):
        self.assertEqual((25.0, 50.0), (self.comparison.intended['setup'].launch_time,
                                        self.comparison.intended['setup'].capture_time))
        self.assertEqual(-25.0, self.comparison.intended['hold'].relationship)

    def test_reported_edges(self):
        self.assertEqual(10.0, self.comparison.reported['setup'].relationship)
        # Aligned to the intended hold capture edge a (0 ns).
        self.assertEqual((0.0, 0.0), (self.comparison.reported['hold'].launch_time,
                                      self.comparison.reported['hold'].capture_time))
        self.assertEqual('edge 1', self.comparison.reported['hold'].launch_label)
        self.assertEqual('a', self.comparison.reported['hold'].capture_label)

    def test_mismatch_detected(self):
        self.assertFalse(self.comparison.matches('setup'))
        self.assertFalse(self.comparison.matches('hold'))
        self.assertFalse(self.comparison.all_match)

    def test_unknown_pin(self):
        oPath = load('dac_spi.setup.rpt')
        oPath.destination = 'NOT_A_PIN'
        oPath.source = 'nothing/C'
        self.assertIsNone(intent.compare({'device': {'interface': []}}, oPath, load('dac_spi.hold.rpt')))


class TestDifferences(unittest.TestCase):

    def setUp(self):
        self.dConfig = utils.read_config_file(os.path.join(sRoot, 'tests', 'analysis', 'config_edge6.yaml'))
        self.setup = load('dac_spi.setup.rpt')
        self.hold = load('dac_spi.hold.rpt')

    def test_report_directions_parsed(self):
        self.assertEqual(('rise', 'rise'), (self.setup.launch_direction, self.setup.capture_direction))

    def test_falling_intent_flags_the_report(self):
        oComparison = intent.compare(self.dConfig, self.setup, self.hold)
        self.assertEqual(['expected +25.000 ns', 'launches on rising edge, expected falling'],
                         oComparison.differences('setup'))

    def test_matching_intent_is_clean(self):
        dPin = self.dConfig['device']['interface'][0]['DAC_DATA']['data']['output'][0]['O_DAC_DATA']
        dPin['launch_clock']['edge'] = 9
        oComparison = intent.compare(self.dConfig, self.setup, self.hold)
        self.assertTrue(oComparison.matches('setup'))
        self.assertEqual(['expected -40.000 ns'], oComparison.differences('hold'))
