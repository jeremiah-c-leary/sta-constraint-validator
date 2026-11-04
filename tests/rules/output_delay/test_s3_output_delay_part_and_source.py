from tests.rules import vsc8540et_changes
from tests.rules import vsc8540et_rule_test_case


class PartClockTestCase(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):
    '''
    O_MII_TX_EN is an SDR-SS-RT-DO output: output delay = data trace + part setup + clock trace.
    The example's maximum is 1.2 + 15 + 1.2 = 17.4 ns, and its minimum 0.8 - 0 + 0.8 = 1.6 ns.
    '''

    sInterface = 'mii'
    sPort = 'O_MII_TX_EN'
    sMethodology = 'SDR-SS-RT-DO'
    lLongerDataTrace = [vsc8540et_changes.lengthen_trace('mii_tx_en', 'O_MII_TX_EN', 'TX_EN', 'device_to_part')]
    sTimingReport = f'{vsc8540et_rule_test_case.sTimingReportDir}/O_MII_TX_EN_timing.rpt'


class TestPartClockMaximum(PartClockTestCase):

    sRuleId = 's3_output_delay_003'

    def test_passes_when_the_maximum_output_delay_matches_the_calculation(self):
        self.assertEqual(0, self.execute())
        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_the_data_trace_differs(self):
        self.execute(lTracesChanges=self.lLongerDataTrace)

        self.assertEqual(f'{self.sTimingReport}:24  Calculated maximum output delay is 18.400ns while actual output delay is 17.400ns', self.get_failure_text(self.sRuleId))

    def test_fails_when_the_clock_trace_differs(self):
        self.execute(lTracesChanges=[('device_pin = "I_MII_TX_CLK"\npart_pin = "MII_TXCLK"\npart_to_device = {max_delay = 1.2', 'device_pin = "I_MII_TX_CLK"\npart_pin = "MII_TXCLK"\npart_to_device = {max_delay = 2.2')])

        self.assert_rule_failed(self.sRuleId)


class TestPartClockMinimum(PartClockTestCase):

    sRuleId = 's3_output_delay_004'

    def test_passes_when_the_minimum_output_delay_matches_the_calculation(self):
        self.execute()
        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_the_data_trace_differs(self):
        self.execute(lTracesChanges=self.lLongerDataTrace)

        self.assertEqual(f'{self.sTimingReport}:138  Calculated minimum output delay is 2.600ns while actual output delay is 1.600ns', self.get_failure_text(self.sRuleId))


class SourceClockTestCase(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):
    '''
    O_RMII_TX_EN is an SDR-SYS-O output: output delay = data trace + part setup - source to part clock trace + source to device clock trace.
    The example's maximum is 1.2 + 4 - 0.4 + 1.4 = 6.2 ns, and its minimum 0.8 - 2 - 0.6 + 1.0 = -0.8 ns.
    '''

    sInterface = 'rmii'
    sPort = 'O_RMII_TX_EN'
    sMethodology = 'SDR-SYS-O'
    lLongerDataTrace = [vsc8540et_changes.lengthen_trace('rmii_tx_en', 'O_RMII_TX_EN', 'TX_EN', 'device_to_part')]
    sTimingReport = f'{vsc8540et_rule_test_case.sTimingReportDir}/O_RMII_TX_EN_timing.rpt'


class TestSourceClockMaximum(SourceClockTestCase):

    sRuleId = 's3_output_delay_005'

    def test_passes_when_the_maximum_output_delay_matches_the_calculation(self):
        self.assertEqual(0, self.execute())
        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_the_data_trace_differs(self):
        self.execute(lTracesChanges=self.lLongerDataTrace)

        self.assertEqual(f'{self.sTimingReport}:24  Calculated maximum output delay is 7.200ns while actual output delay is 6.200ns', self.get_failure_text(self.sRuleId))

    def test_fails_when_the_part_setup_differs(self):
        self.execute(lPartChanges=[('setup = {value = 4, symbol = "TSU"', 'setup = {value = 5, symbol = "TSU"')])

        self.assert_rule_failed(self.sRuleId)


class TestSourceClockMinimum(SourceClockTestCase):

    sRuleId = 's3_output_delay_006'

    def test_passes_when_the_minimum_output_delay_matches_the_calculation(self):
        self.execute()
        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_the_data_trace_differs(self):
        self.execute(lTracesChanges=self.lLongerDataTrace)

        self.assertEqual(f'{self.sTimingReport}:138  Calculated minimum output delay is 0.200ns while actual output delay is -0.800ns', self.get_failure_text(self.sRuleId))
