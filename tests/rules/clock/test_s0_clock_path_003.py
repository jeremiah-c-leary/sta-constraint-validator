from tests.rules import vsc8540et_rule_test_case

RULE_ID = 's0_clock_path_003'


class TestInput(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):
    '''
    The capture clock path of every I_MII_RX_DV timing report starts at the clock port, I_MII_RX_CLK.
    The file holds eight reports, and the first element of each capture clock path is on these lines.
    '''

    sInterface = 'mii'
    sPort = 'I_MII_RX_DV'
    sMethodology = 'SDR-SS-I'
    lClockPathStartLines = [48, 97, 162, 211, 276, 325, 390, 439]
    lMovedClock = [('I_MII_RX_CLK (IN)', 'I_CLK (IN)'), ('    I_MII_RX_CLK\n', '    I_CLK\n')]

    def test_passes_when_the_capture_clock_path_starts_at_the_clock_port(self):
        self.execute()
        self.assert_rule_passed(RULE_ID)

    def test_fails_when_the_capture_clock_path_starts_at_another_port(self):
        self.execute(sReport='I_MII_RX_DV_timing.rpt', lReportChanges=self.lMovedClock)

        lExpected = []
        for iLine in self.lClockPathStartLines:
            lExpected.append(f'{self.sChangedTimingReport}:{iLine}  capture clock path starts at I_CLK, configured clock port I_MII_RX_CLK')
        self.assertEqual('\n'.join(lExpected), self.get_failure_text(RULE_ID))

    def test_fails_when_the_configured_clock_port_differs(self):
        self.execute(lInterfaceChanges=[('port = "I_MII_RX_CLK"', 'port = "I_MII_RX_CLK_2"')])

        self.assert_rule_failed(RULE_ID)


class TestOutput(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):
    '''
    The launch clock path of every O_MII_TX_EN timing report starts at the clock port, I_MII_TX_CLK.
    '''

    sInterface = 'mii'
    sPort = 'O_MII_TX_EN'
    sMethodology = 'SDR-SS-RT-DO'

    def test_passes_when_the_launch_clock_path_starts_at_the_clock_port(self):
        self.execute()
        self.assert_rule_passed(RULE_ID)

    def test_fails_when_the_launch_clock_path_starts_at_another_port(self):
        self.execute(sReport='O_MII_TX_EN_timing.rpt', lReportChanges=[('I_MII_TX_CLK (IN)', 'I_CLK (IN)'), ('    I_MII_TX_CLK\n', '    I_CLK\n')])

        sFirstDetail = self.get_failure_text(RULE_ID).split('\n')[0]
        self.assertEqual(f'{self.sChangedTimingReport}:39  launch clock path starts at I_CLK, configured clock port I_MII_TX_CLK', sFirstDetail)
