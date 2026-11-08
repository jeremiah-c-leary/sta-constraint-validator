from tests.rules import vsc8540et_rule_test_case

# Every timing report of the uncompensated RGMII ports times both edges of the clock that crosses the board.
lRisingOnlyInput = [('rgmii_rxc fall@', 'rgmii_rxc rise@')]
lRisingOnlyOutput = [('rgmii_txc fall@', 'rgmii_txc rise@')]
# The first setup report of I_RGMII_RX_CTL times fall to fall; this makes it, and the other reports with the same requirement, fall to rise.
lFallToRise = [('(rgmii_rxc fall@20.000ns - rgmii_rxc fall@20.000ns)\n  Data Path Delay:', '(rgmii_rxc rise@40.000ns - rgmii_rxc fall@20.000ns)\n  Data Path Delay:')]


class InputTestCase(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):

    sInterface = 'rgmii'
    sPort = 'I_RGMII_RX_CTL'
    sMethodology = 'DDR-SS-I-SE'


class TestBothEdgesOfAnInput(InputTestCase):

    sRuleId = 's4_edge_001'

    def test_passes_when_both_edges_of_the_launch_clock_are_timed(self):
        self.execute()
        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_only_the_rising_edges_are_timed(self):
        self.execute(sReport='I_RGMII_RX_CTL_timing.rpt', lReportChanges=lRisingOnlyInput)

        lExpected = []
        lExpected.append(f'{self.sChangedTimingReport}:21  setup timing reports time only the rise edges of rgmii_rxc')
        lExpected.append(f'{self.sChangedTimingReport}:237  hold timing reports time only the rise edges of rgmii_rxc')
        self.assertEqual('\n'.join(lExpected), self.get_failure_text(self.sRuleId))


class TestBothEdgesOfAnOutput(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):

    sInterface = 'rgmii'
    sPort = 'O_RGMII_TX_CTL'
    sMethodology = 'DDR-SS-O'
    sRuleId = 's4_edge_001'

    def test_passes_when_both_edges_of_the_capture_clock_are_timed(self):
        self.execute()
        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_only_the_rising_edges_are_timed(self):
        self.execute(sReport='O_RGMII_TX_CTL_timing.rpt', lReportChanges=lRisingOnlyOutput)

        self.assertEqual(f'{self.sChangedTimingReport}:21  setup timing reports time only the rise edges of rgmii_txc', self.get_failure_text(self.sRuleId).split('\n')[0])


class TestEdgePairs(InputTestCase):

    sRuleId = 's4_edge_002'

    def test_passes_when_every_report_pairs_the_same_edge_capture_edges(self):
        self.execute()
        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_a_setup_report_times_the_other_edge_type(self):
        self.execute(sReport='I_RGMII_RX_CTL_timing.rpt', lReportChanges=lFallToRise)

        sExpected = f'{self.sChangedTimingReport}:21  setup timing report times fall to rise; a DDR-SS-I-SE port captures each bit on the edge it is aligned with, so its setup timing reports time the same edge type'
        self.assertEqual(sExpected, self.get_failure_text(self.sRuleId).split('\n')[0])

    def test_the_requirement_rule_passes_the_wrong_pair(self):
        # The wrong pair gives the same requirement, which is why the edge pairs have a rule of their own.
        self.execute(sReport='I_RGMII_RX_CTL_timing.rpt', lReportChanges=lFallToRise)

        self.assert_rule_passed('s4_requirement_001')

    def test_next_edge_port_fails_on_same_edge_reports(self):
        # The edges are changed to a next edge capture, so the interface is valid, but the reports still time the same edge.
        lNextEdge = [('methodology = "DDR-SS-I-SE"\nlaunch_clock = {name = "rgmii_rxc", setup_edge = 2, hold_edge = 2}\ncapture_clock = {name = "rgmii_rxc", setup_edge = 2, hold_edge = 1}\nregisters = ["GEN_RGMII_RX[4].U_IDDR"]', 'methodology = "DDR-SS-I-NE"\nlaunch_clock = {name = "rgmii_rxc", setup_edge = 0, hold_edge = 0}\ncapture_clock = {name = "rgmii_rxc", setup_edge = 1, hold_edge = 0}\nregisters = ["GEN_RGMII_RX[4].U_IDDR"]')]
        self.sSuiteName = 'I_RGMII_RX_CTL.DDR-SS-I-NE'
        self.execute(lInterfaceChanges=lNextEdge)

        sExpected = f'{vsc8540et_rule_test_case.sTimingReportDir}/I_RGMII_RX_CTL_timing.rpt:21  setup timing report times fall to fall; a DDR-SS-I-NE port captures each bit on the edge after the one it is launched on, so its setup timing reports time the other edge type'
        self.assertEqual(sExpected, self.get_failure_text(self.sRuleId).split('\n')[0])
