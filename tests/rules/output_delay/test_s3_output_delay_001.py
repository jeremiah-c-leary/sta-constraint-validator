import os

from tests.rules import rule_test_case

sTestDir = os.path.dirname(os.path.abspath(__file__))
sParseDir = os.path.join(sTestDir, '..', '..', 'timing_report', 'parse', 'vivado')

# Setup reports at both process corners have an output delay of 2.000ns.
# Hold reports at both process corners have an output delay of 1.000ns.
sTimingReport = os.path.abspath(os.path.join(sParseDir, 'O_DAC_DATA_timing.rpt'))

sRuleId = 's3_output_delay_001'

# With these traces, a part setup of 0.5 gives a calculated maximum output delay of:
#    0.5 + 2.0 - 0.5 = 2.000
# and a part hold of 0.5 gives a calculated minimum output delay of:
#   -0.5 + 2.0 - 0.5 = 1.000
fPassingSetup = 0.5
fPassingHold = 0.5


def create_trace(sName, sDevicePin, sPartPin, fMaxDelay, fMinDelay):
    dTrace = {}
    dTrace['name'] = sName
    dTrace['device_pin'] = sDevicePin
    dTrace['part_pin'] = sPartPin
    dTrace['max_delay'] = fMaxDelay
    dTrace['min_delay'] = fMinDelay
    return dTrace


def create_data_trace(fMaxDelay, fMinDelay):
    return create_trace('data_output', 'O_DAC_DATA', 'SDIN', fMaxDelay, fMinDelay)


def create_clock_trace(fMaxDelay, fMinDelay):
    return create_trace('clock', 'O_DAC_SCLK', 'SCLK', fMaxDelay, fMinDelay)


def create_passing_traces():
    lTraces = []
    lTraces.append(create_data_trace(2.0, 2.0))
    lTraces.append(create_clock_trace(0.5, 0.5))
    return lTraces


def build_config_text(sPartFile, sTracesFile):
    lText = []
    lText.append('description = "s3_output_delay_001 test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[clock]]')
    lText.append('name = "clk_100mhz"')
    lText.append('period = 10.000')
    lText.append('[[clock]]')
    lText.append('name = "dac_sclk"')
    lText.append('period = 50')
    lText.append('port = "O_DAC_SCLK"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
    lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
    lText.append(f'timing_reports = ["{sTimingReport}"]')
    return '\n'.join(lText)


def build_traces_text(lTraces):
    lText = []
    for dTrace in lTraces:
        lText.append('[[trace]]')
        lText.append(f'name = "{dTrace["name"]}"')
        lText.append(f'device_pin = "{dTrace["device_pin"]}"')
        lText.append(f'part_pin = "{dTrace["part_pin"]}"')
        lText.append(f'device_to_part = {{max_delay = {dTrace["max_delay"]}, min_delay = {dTrace["min_delay"]}}}')
    return '\n'.join(lText)


class Test(rule_test_case.RuleTestCase):

    def execute(self, fSetup, fHold, lTraces):
        rule_test_case.write_file(self.sInterfaceFile, build_config_text(self.sPartFile, self.sTracesFile))
        rule_test_case.write_file(self.sPartFile, rule_test_case.build_part_text('Rising', fSetup, fHold))
        rule_test_case.write_file(self.sTracesFile, build_traces_text(lTraces))
        return self.run_check()

    def test_passes_when_output_delay_matches_calculated_output_delay(self):
        self.execute(fPassingSetup, fPassingHold, create_passing_traces())

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_output_delay_matches_calculated_output_delay(self):
        iExitCode = self.execute(fPassingSetup, fPassingHold, create_passing_traces())

        self.assertEqual(0, iExitCode)

    def test_fails_when_part_setup_moves_calculated_output_delay(self):
        self.execute(10.0, fPassingHold, create_passing_traces())

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_output_delay_does_not_match(self):
        iExitCode = self.execute(10.0, fPassingHold, create_passing_traces())

        self.assertEqual(1, iExitCode)

    def test_passes_when_calculated_output_delay_is_above_by_less_than_rounding(self):
        # 0.5004 + 2.0 - 0.5 = 2.0004
        self.execute(0.5004, fPassingHold, create_passing_traces())

        self.assert_rule_passed(sRuleId)

    def test_passes_when_calculated_output_delay_is_below_by_less_than_rounding(self):
        # 0.4996 + 2.0 - 0.5 = 1.9996
        self.execute(0.4996, fPassingHold, create_passing_traces())

        self.assert_rule_passed(sRuleId)

    def test_fails_when_calculated_output_delay_is_above_by_more_than_rounding(self):
        # 0.5006 + 2.0 - 0.5 = 2.0006
        self.execute(0.5006, fPassingHold, create_passing_traces())

        self.assert_rule_failed(sRuleId)

    def test_fails_when_calculated_output_delay_is_below_by_more_than_rounding(self):
        # 0.4994 + 2.0 - 0.5 = 1.9994
        self.execute(0.4994, fPassingHold, create_passing_traces())

        self.assert_rule_failed(sRuleId)

    def test_uses_maximum_delay_of_data_trace(self):
        # 0.5 + 2.5 - 0.5 = 2.500
        lTraces = []
        lTraces.append(create_data_trace(2.5, 2.0))
        lTraces.append(create_clock_trace(0.5, 0.5))
        self.execute(fPassingSetup, fPassingHold, lTraces)

        self.assert_rule_failed(sRuleId)

    def test_uses_minimum_delay_of_clock_trace(self):
        # 0.5 + 2.0 - 0.0 = 2.500
        lTraces = []
        lTraces.append(create_data_trace(2.0, 2.0))
        lTraces.append(create_clock_trace(0.5, 0.0))
        self.execute(fPassingSetup, fPassingHold, lTraces)

        self.assert_rule_failed(sRuleId)

    def test_ignores_part_hold_and_hold_trace_delays(self):
        # Setup:  0.5 + 2.0 - 0.5 = 2.000, which matches
        # Hold:  -9.0 + 0.0 - 3.0 = -12.000, which is checked by s3_output_delay_002
        lTraces = []
        lTraces.append(create_data_trace(2.0, 0.0))
        lTraces.append(create_clock_trace(3.0, 0.5))
        self.execute(fPassingSetup, 9.0, lTraces)

        self.assert_rule_passed(sRuleId)

    def test_finds_data_trace_by_device_pin(self):
        lTraces = []
        lTraces.append(create_trace('other_output', 'O_OTHER_DATA', 'SDO', 9.0, 9.0))
        lTraces.extend(create_passing_traces())
        self.execute(fPassingSetup, fPassingHold, lTraces)

        self.assert_rule_passed(sRuleId)

    def test_finds_clock_trace_by_clock_pin_of_part_pin(self):
        lTraces = []
        lTraces.append(create_data_trace(2.0, 2.0))
        lTraces.append(create_trace('chip_select', 'O_DAC_CSF', 'CSF', 9.0, 9.0))
        lTraces.append(create_clock_trace(0.5, 0.5))
        self.execute(fPassingSetup, fPassingHold, lTraces)

        self.assert_rule_passed(sRuleId)
