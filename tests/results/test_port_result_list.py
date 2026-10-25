import unittest

from stacv.interface import config
from stacv.results import port_result
from stacv.results import port_result_list

from tests.results.methodology_results_builder import build_failing_methodology_results
from tests.results.methodology_results_builder import build_passing_methodology_results


def build_port_result(sName, oMethodologyResults):
    oPort = config.Port()
    oPort.name = sName
    oPort.methodology = 'SDR-SS-O'
    return port_result.PortResult(oPort, oMethodologyResults)


class Test(unittest.TestCase):

    def setUp(self):
        self.oFirstPassingResult = build_port_result('O_DAC_DATA', build_passing_methodology_results())
        self.oSecondPassingResult = build_port_result('O_DAC_SCLK', build_passing_methodology_results())
        self.oFailingResult = build_port_result('O_DAC_CSF', build_failing_methodology_results())

    def test_new_port_result_list_is_empty(self):
        oPortResults = port_result_list.PortResultList()

        self.assertEqual([], oPortResults.results)

    def test_add_keeps_results_in_order(self):
        oPortResults = port_result_list.PortResultList()

        oPortResults.add_result(self.oFirstPassingResult)
        oPortResults.add_result(self.oFailingResult)
        oPortResults.add_result(self.oSecondPassingResult)

        lExpected = [self.oFirstPassingResult, self.oFailingResult, self.oSecondPassingResult]
        self.assertEqual(lExpected, oPortResults.results)

    def test_has_failures_when_any_port_fails(self):
        oPortResults = port_result_list.PortResultList()

        oPortResults.add_result(self.oFirstPassingResult)
        oPortResults.add_result(self.oFailingResult)
        oPortResults.add_result(self.oSecondPassingResult)

        self.assertTrue(oPortResults.has_failures())

    def test_has_no_failures_when_every_port_passes(self):
        oPortResults = port_result_list.PortResultList()

        oPortResults.add_result(self.oFirstPassingResult)
        oPortResults.add_result(self.oSecondPassingResult)

        self.assertFalse(oPortResults.has_failures())

    def test_empty_list_has_no_failures(self):
        oPortResults = port_result_list.PortResultList()

        self.assertFalse(oPortResults.has_failures())
