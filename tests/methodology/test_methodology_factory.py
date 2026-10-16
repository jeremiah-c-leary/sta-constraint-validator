import unittest

from stacv.methodology import methodology_factory
from stacv.methodology import sdr_source_synchronous_output


class Test(unittest.TestCase):

    def test_create_methodology_returns_sdr_source_synchronous_output_for_sdr_ss_o(self):
        oMethodology = methodology_factory.create_methodology('SDR-SS-O')
        self.assertIsInstance(oMethodology, sdr_source_synchronous_output.SdrSourceSynchronousOutput)

    def test_create_methodology_returns_a_new_object_on_every_call(self):
        oFirstMethodology = methodology_factory.create_methodology('SDR-SS-O')
        oSecondMethodology = methodology_factory.create_methodology('SDR-SS-O')
        self.assertIsNot(oFirstMethodology, oSecondMethodology)
