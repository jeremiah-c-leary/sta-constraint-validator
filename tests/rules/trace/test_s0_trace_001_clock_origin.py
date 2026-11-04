from tests.rules import vsc8540et_rule_test_case

RULE_ID = 's0_trace_001'


class TestPartClock(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):
    '''
    The part sends the clock of I_MII_RX_DV, so its clock trace runs from the part's RX_CLK to the device's I_MII_RX_CLK.
    '''

    sInterface = 'mii'
    sPort = 'I_MII_RX_DV'
    sMethodology = 'SDR-SS-I'

    def test_passes_when_the_clock_trace_from_the_part_exists(self):
        self.execute()
        self.assert_rule_passed(RULE_ID)

    def test_fails_when_no_clock_trace_runs_from_the_part_to_the_clock_port(self):
        self.execute(lTracesChanges=[('device_pin = "I_MII_RX_CLK"', 'device_pin = "I_MII_RX_CLK_2"')])

        self.assertEqual('a clock trace does not run from part pin RX_CLK to device pin I_MII_RX_CLK', self.get_failure_text(RULE_ID))


class TestSourceClock(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):
    '''
    A clock source drives the clock of I_RMII_CRS_DV, with one trace to the device's I_RMII_REF_CLK and one to the part's RMII_CLKIN.
    '''

    sInterface = 'rmii'
    sPort = 'I_RMII_CRS_DV'
    sMethodology = 'SDR-SYS-I'

    def test_passes_when_both_clock_traces_from_the_source_exist(self):
        self.execute()
        self.assert_rule_passed(RULE_ID)

    def test_fails_when_no_clock_trace_runs_from_a_source_to_the_clock_port(self):
        self.execute(lTracesChanges=[('device_pin = "I_RMII_REF_CLK"', 'device_pin = "I_RMII_REF_CLK_2"')])

        self.assertEqual('a clock trace does not run from a clock source to device pin I_RMII_REF_CLK', self.get_failure_text(RULE_ID))

    def test_fails_when_no_clock_trace_runs_from_the_source_to_the_part(self):
        self.execute(lTracesChanges=[('part_pin = "RMII_CLKIN"\n', 'part_pin = "RMII_CLKIN_2"\n')])

        self.assertEqual('a clock trace does not run from the clock source of device pin I_RMII_REF_CLK to part pin RMII_CLKIN', self.get_failure_text(RULE_ID))
