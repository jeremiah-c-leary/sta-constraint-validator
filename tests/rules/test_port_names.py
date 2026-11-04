import unittest

from stacv.rules import port_names


class TestMatchesConfiguredPort(unittest.TestCase):

    def test_a_port_matches_its_own_name(self):
        self.assertTrue(port_names.matches_configured_port('O_DAC_DATA', 'O_DAC_DATA'))

    def test_a_port_does_not_match_another_name(self):
        self.assertFalse(port_names.matches_configured_port('O_DAC_CSF', 'O_DAC_DATA'))

    def test_each_bit_of_a_bus_matches_the_bus(self):
        for sBit in ['O_MII_TXD[0]', 'O_MII_TXD[1]', 'O_MII_TXD[2]', 'O_MII_TXD[3]']:
            with self.subTest(bit=sBit):
                self.assertTrue(port_names.matches_configured_port(sBit, 'O_MII_TXD[3:0]'))

    def test_a_bit_outside_the_bus_does_not_match(self):
        self.assertFalse(port_names.matches_configured_port('O_MII_TXD[4]', 'O_MII_TXD[3:0]'))

    def test_a_bus_written_lower_to_upper_matches_its_bits(self):
        self.assertTrue(port_names.matches_configured_port('O_BUS[1]', 'O_BUS[0:3]'))

    def test_a_bit_of_another_bus_does_not_match(self):
        self.assertFalse(port_names.matches_configured_port('O_RMII_TXD[1]', 'O_MII_TXD[3:0]'))

    def test_the_bus_name_alone_does_not_match(self):
        self.assertFalse(port_names.matches_configured_port('O_MII_TXD', 'O_MII_TXD[3:0]'))
