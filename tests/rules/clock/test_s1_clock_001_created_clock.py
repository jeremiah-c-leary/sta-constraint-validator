from tests.rules import vsc8540et_rule_test_case

RULE_ID = 's1_clock_001'


class TestInputOnAPartClock(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):
    '''
    The input delay of I_MII_RX_DV is measured from the clock at the port it is created on, so its launch clock path is empty.
    '''

    sInterface = 'mii'
    sPort = 'I_MII_RX_DV'
    sMethodology = 'SDR-SS-I'

    def test_passes_when_the_launch_clock_path_is_empty(self):
        self.execute()
        self.assert_rule_passed(RULE_ID)


class TestOutputOnAPartClock(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):
    '''
    The output delay of O_MII_TX_EN is measured from the clock at the port it is created on, so its capture clock path is empty.
    '''

    sInterface = 'mii'
    sPort = 'O_MII_TX_EN'
    sMethodology = 'SDR-SS-RT-DO'

    def test_passes_when_the_capture_clock_path_is_empty(self):
        self.execute()
        self.assert_rule_passed(RULE_ID)
