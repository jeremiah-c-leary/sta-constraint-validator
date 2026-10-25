import unittest

from stacv.interface import config
from stacv.results import port_result

from tests.results.methodology_results_builder import build_failing_methodology_results
from tests.results.methodology_results_builder import build_passing_methodology_results


def build_port(sName, sMethodology):
    oPort = config.Port()
    oPort.name = sName
    oPort.methodology = sMethodology
    return oPort


class Test(unittest.TestCase):

    def setUp(self):
        self.oPort = build_port('O_DAC_DATA', 'SDR-SS-O')

    def test_port_result_keeps_its_port(self):
        oMethodologyResults = build_passing_methodology_results()

        oPortResult = port_result.PortResult(self.oPort, oMethodologyResults)

        self.assertIs(self.oPort, oPortResult.port)

    def test_port_result_keeps_its_methodology_results(self):
        oMethodologyResults = build_passing_methodology_results()

        oPortResult = port_result.PortResult(self.oPort, oMethodologyResults)

        self.assertIs(oMethodologyResults, oPortResult.methodology_results)

    def test_port_result_has_failures_when_a_rule_fails(self):
        oPortResult = port_result.PortResult(self.oPort, build_failing_methodology_results())

        self.assertTrue(oPortResult.has_failures())

    def test_port_result_has_no_failures_when_every_rule_passes(self):
        oPortResult = port_result.PortResult(self.oPort, build_passing_methodology_results())

        self.assertFalse(oPortResult.has_failures())
