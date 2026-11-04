from tests.rules import vsc8540et_rule_test_case


class TestOutputBus(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):
    '''
    O_MII_TXD[3:0] is reported one bit at a time, so its data paths end at O_MII_TXD[0] to O_MII_TXD[3].
    '''

    sInterface = 'mii'
    sPort = 'O_MII_TXD[3:0]'
    sMethodology = 'SDR-SS-RT-DO'

    def test_passes_when_every_data_path_ends_at_a_bit_of_the_bus(self):
        self.execute()
        self.assert_rule_passed('s0_data_path_001')

    def test_fails_when_a_data_path_ends_at_a_bit_outside_the_bus(self):
        self.execute(lInterfaceChanges=[('name = "O_MII_TXD[3:0]"', 'name = "O_MII_TXD[2:0]"')])
        self.sSuiteName = 'O_MII_TXD[2:0].SDR-SS-RT-DO'

        self.assertIn('data path ends at O_MII_TXD[3], configured port O_MII_TXD[2:0]', self.get_failure_text('s0_data_path_001'))


class TestInputBus(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):

    sInterface = 'mii'
    sPort = 'I_MII_RXD[3:0]'
    sMethodology = 'SDR-SS-I'

    def test_passes_when_every_data_path_starts_at_a_bit_of_the_bus(self):
        self.execute()
        self.assert_rule_passed('s0_data_path_002')
