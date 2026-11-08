from tests.rules import rule_test_case

# Setup reports at both process corners have an output delay of 12.000ns.
# Hold reports at both process corners have an output delay of -12.000ns.
sTimingReport = rule_test_case.sTimingReport

sRuleId = 's3_output_delay_001'

# With these traces, a part setup of 10 gives a calculated maximum output delay of:
#    10.0 + 3.0 - 1.0 = 12.000
# and a part hold of 10 gives a calculated minimum output delay of:
#   -10.0 + 1.0 - 3.0 = -12.000
fPassingSetup = 10.0
fPassingHold = 10.0


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
    lTraces.append(create_data_trace(3.0, 1.0))
    lTraces.append(create_clock_trace(3.0, 1.0))
    return lTraces


def build_config_text(sPartFile, sTracesFile):
    lText = []
    lText.append('description = "s3_output_delay_001 test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append('part_interface = "Serial Interface"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[clock]]')
    lText.append('name = "clk_100mhz"')
    lText.append('period = 10.000')
    lText.append('[[clock]]')
    lText.append('name = "dac_sclk"')
    lText.append('period = 40.0')
    lText.append('port = "O_DAC_SCLK"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 8}')
    lText.append('capture_clock = {name = "dac_sclk", setup_edge = 3, hold_edge = 1}')
    lText.append('registers = ["q_spi_output_data_reg"]')
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
        rule_test_case.write_file(self.sPartFile, rule_test_case.build_part_text('Falling', fSetup, fHold))
        rule_test_case.write_file(self.sTracesFile, build_traces_text(lTraces))
        return self.run_check()

    def test_passes_when_output_delay_matches_calculated_output_delay(self):
        self.execute(fPassingSetup, fPassingHold, create_passing_traces())

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_output_delay_matches_calculated_output_delay(self):
        iExitCode = self.execute(fPassingSetup, fPassingHold, create_passing_traces())

        self.assertEqual(0, iExitCode)

    def test_fails_when_part_setup_moves_calculated_output_delay(self):
        # 5.0 + 3.0 - 1.0 = 7.000
        self.execute(5.0, fPassingHold, create_passing_traces())

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_output_delay_does_not_match(self):
        iExitCode = self.execute(5.0, fPassingHold, create_passing_traces())

        self.assertEqual(1, iExitCode)

    def test_passes_when_calculated_output_delay_is_above_by_less_than_rounding(self):
        # 10.0004 + 3.0 - 1.0 = 12.0004
        self.execute(10.0004, fPassingHold, create_passing_traces())

        self.assert_rule_passed(sRuleId)

    def test_passes_when_calculated_output_delay_is_below_by_less_than_rounding(self):
        # 9.9996 + 3.0 - 1.0 = 11.9996
        self.execute(9.9996, fPassingHold, create_passing_traces())

        self.assert_rule_passed(sRuleId)

    def test_fails_when_calculated_output_delay_is_above_by_more_than_rounding(self):
        # 10.0006 + 3.0 - 1.0 = 12.0006
        self.execute(10.0006, fPassingHold, create_passing_traces())

        self.assert_rule_failed(sRuleId)

    def test_fails_when_calculated_output_delay_is_below_by_more_than_rounding(self):
        # 9.9994 + 3.0 - 1.0 = 11.9994
        self.execute(9.9994, fPassingHold, create_passing_traces())

        self.assert_rule_failed(sRuleId)

    def test_uses_maximum_delay_of_data_trace(self):
        # 10.0 + 3.5 - 1.0 = 12.500
        lTraces = []
        lTraces.append(create_data_trace(3.5, 1.0))
        lTraces.append(create_clock_trace(3.0, 1.0))
        self.execute(fPassingSetup, fPassingHold, lTraces)

        self.assert_rule_failed(sRuleId)

    def test_uses_minimum_delay_of_clock_trace(self):
        # 10.0 + 3.0 - 0.5 = 12.500
        lTraces = []
        lTraces.append(create_data_trace(3.0, 1.0))
        lTraces.append(create_clock_trace(3.0, 0.5))
        self.execute(fPassingSetup, fPassingHold, lTraces)

        self.assert_rule_failed(sRuleId)

    def test_ignores_part_hold_and_hold_trace_delays(self):
        # Setup:  10.0 + 3.0 - 1.0 = 12.000, which matches
        # Hold:   -5.0 + 0.0 - 4.0 = -9.000, which is checked by s3_output_delay_002
        lTraces = []
        lTraces.append(create_data_trace(3.0, 0.0))
        lTraces.append(create_clock_trace(4.0, 1.0))
        self.execute(fPassingSetup, 5.0, lTraces)

        self.assert_rule_passed(sRuleId)

    def test_finds_data_trace_by_device_pin(self):
        lTraces = []
        lTraces.append(create_trace('other_output', 'O_OTHER_DATA', 'SDO', 9.0, 9.0))
        lTraces.extend(create_passing_traces())
        self.execute(fPassingSetup, fPassingHold, lTraces)

        self.assert_rule_passed(sRuleId)

    def test_finds_clock_trace_by_clock_pin_of_part_pin(self):
        lTraces = []
        lTraces.append(create_data_trace(3.0, 1.0))
        lTraces.append(create_trace('chip_select', 'O_DAC_CSF', 'CSF', 9.0, 9.0))
        lTraces.append(create_clock_trace(3.0, 1.0))
        self.execute(fPassingSetup, fPassingHold, lTraces)

        self.assert_rule_passed(sRuleId)
