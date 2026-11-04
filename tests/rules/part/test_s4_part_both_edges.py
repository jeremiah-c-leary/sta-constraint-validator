from tests.rules import vsc8540et_rule_test_case

# The uncompensated RGMII part pins take data on both edges.
sTxCtlBoth = 'name = "TX_CTL"\nmethodology = "DDR-SS-I"\nclock = {pin = "TX_CLK", max_frequency = 25, duty_cycle = {min = 40, max = 60}}\ncapture_edge = "Both"'
sRxCtlBoth = 'name = "RX_CTL"\nmethodology = "DDR-SS-O"\nclock = {pin = "RX_CLK", max_frequency = 25, duty_cycle = {min = 40, max = 60}}\ncko_max = {value = 0.5, symbol = "tSKEWT", source = "Table 7-25"}\ncko_min = {value = -0.5, symbol = "tSKEWT", source = "Table 7-25"}\nlaunch_edge = "Both"'


class TestCaptureOnBothEdges(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):

    sInterface = 'rgmii'
    sPort = 'O_RGMII_TX_CTL'
    sMethodology = 'DDR-SS-O'
    sRuleId = 's4_part_001'

    def test_passes_when_the_part_captures_on_both_edges(self):
        self.execute()
        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_the_part_captures_only_on_the_rising_edge(self):
        self.execute(lPartChanges=[(sTxCtlBoth, sTxCtlBoth.replace('"Both"', '"Rising"'))])

        self.assertIn('capture clock edge fall, part TX_CTL captures on Rising', self.get_failure_text(self.sRuleId))


class TestLaunchOnBothEdges(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):

    sInterface = 'rgmii'
    sPort = 'I_RGMII_RX_CTL'
    sMethodology = 'DDR-SS-I-SE'
    sRuleId = 's4_part_002'

    def test_passes_when_the_part_launches_on_both_edges(self):
        self.execute()
        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_the_part_launches_only_on_the_falling_edge(self):
        self.execute(lPartChanges=[(sRxCtlBoth, sRxCtlBoth.replace('"Both"', '"Falling"'))])

        self.assertIn('launch clock edge rise, part RX_CTL launches on Falling', self.get_failure_text(self.sRuleId))
