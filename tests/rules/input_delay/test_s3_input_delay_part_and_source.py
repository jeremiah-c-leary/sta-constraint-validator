from tests.rules import vsc8540et_changes
from tests.rules import vsc8540et_rule_test_case


class PartClockTestCase(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):
    '''
    I_MII_RX_DV is an SDR-SS-I input: input delay = part clock to out + data trace - clock trace.
    The example's maximum is 30 + 1.2 - 0.8 = 30.4 ns, and its minimum 10 + 0.8 - 1.2 = 9.6 ns.
    '''

    sInterface = 'mii'
    sPort = 'I_MII_RX_DV'
    sMethodology = 'SDR-SS-I'
    lLongerDataTrace = [vsc8540et_changes.lengthen_trace('mii_rx_dv', 'I_MII_RX_DV', 'RX_DV', 'part_to_device')]
    sTimingReport = f'{vsc8540et_rule_test_case.sTimingReportDir}/I_MII_RX_DV_timing.rpt'


class TestPartClockMaximum(PartClockTestCase):

    sRuleId = 's3_input_delay_003'

    def test_passes_when_the_maximum_input_delay_matches_the_calculation(self):
        self.assertEqual(0, self.execute())
        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_the_data_trace_differs(self):
        self.execute(lTracesChanges=self.lLongerDataTrace)

        self.assertEqual(f'{self.sTimingReport}:24  Calculated maximum input delay is 31.400ns while actual input delay is 30.400ns', self.get_failure_text(self.sRuleId))

    def test_fails_when_the_part_clock_to_out_differs(self):
        self.execute(lPartChanges=[('cko_max = {value = 30, symbol = "tDELAY"', 'cko_max = {value = 31, symbol = "tDELAY"')])

        self.assert_rule_failed(self.sRuleId)


class TestPartClockMinimum(PartClockTestCase):

    sRuleId = 's3_input_delay_004'

    def test_passes_when_the_minimum_input_delay_matches_the_calculation(self):
        self.execute()
        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_the_data_trace_differs(self):
        self.execute(lTracesChanges=self.lLongerDataTrace)

        self.assertEqual(f'{self.sTimingReport}:138  Calculated minimum input delay is 10.600ns while actual input delay is 9.600ns', self.get_failure_text(self.sRuleId))


class DoubleDataRateTestCase(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):
    '''
    I_RGMII_RX_CTL is a DDR-SS-I-SE input, which runs the same calculation: 0.5 + 0.8 - 2.6 = -1.3 ns maximum.
    '''

    sInterface = 'rgmii'
    sPort = 'I_RGMII_RX_CTL'
    sMethodology = 'DDR-SS-I-SE'


class TestDoubleDataRate(DoubleDataRateTestCase):

    def test_passes_when_the_input_delays_match_the_calculation(self):
        self.assertEqual(0, self.execute())
        self.assert_rule_passed('s3_input_delay_003')
        self.assert_rule_passed('s3_input_delay_004')


class SourceClockTestCase(vsc8540et_rule_test_case.Vsc8540etRuleTestCase):
    '''
    I_RMII_CRS_DV is an SDR-SYS-I input: input delay = source to part clock trace - source to device clock trace + part clock to out + data trace.
    The example's maximum is 0.6 - 1.0 + 13.5 + 1.2 = 14.3 ns, and its minimum 0.4 - 1.4 + 0 + 0.8 = -0.2 ns.
    '''

    sInterface = 'rmii'
    sPort = 'I_RMII_CRS_DV'
    sMethodology = 'SDR-SYS-I'
    lLongerDataTrace = [vsc8540et_changes.lengthen_trace('rmii_crs_dv', 'I_RMII_CRS_DV', 'CRS_DV', 'part_to_device')]
    sTimingReport = f'{vsc8540et_rule_test_case.sTimingReportDir}/I_RMII_CRS_DV_timing.rpt'


class TestSourceClockMaximum(SourceClockTestCase):

    sRuleId = 's3_input_delay_005'

    def test_passes_when_the_maximum_input_delay_matches_the_calculation(self):
        self.assertEqual(0, self.execute())
        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_the_data_trace_differs(self):
        self.execute(lTracesChanges=self.lLongerDataTrace)

        self.assertEqual(f'{self.sTimingReport}:24  Calculated maximum input delay is 15.300ns while actual input delay is 14.300ns', self.get_failure_text(self.sRuleId))

    def test_fails_when_the_source_to_part_clock_trace_differs(self):
        self.execute(lTracesChanges=[('source_to_part = {max_delay = 0.6, min_delay = 0.4}', 'source_to_part = {max_delay = 1.6, min_delay = 0.4}')])

        self.assert_rule_failed(self.sRuleId)


class TestSourceClockMinimum(SourceClockTestCase):

    sRuleId = 's3_input_delay_006'

    def test_passes_when_the_minimum_input_delay_matches_the_calculation(self):
        self.execute()
        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_the_data_trace_differs(self):
        self.execute(lTracesChanges=self.lLongerDataTrace)

        self.assertEqual(f'{self.sTimingReport}:138  Calculated minimum input delay is 0.800ns while actual input delay is -0.200ns', self.get_failure_text(self.sRuleId))

    def test_fails_when_the_source_to_device_clock_trace_differs(self):
        self.execute(lTracesChanges=[('source_to_device = {max_delay = 1.4, min_delay = 1.0}', 'source_to_device = {max_delay = 2.4, min_delay = 1.0}')])

        self.assert_rule_failed(self.sRuleId)
