from tests.rules import rule_test_case


# Setup reports at both process corners have an output delay of 12.000ns.
# Hold reports at both process corners have an output delay of -12.000ns.
sTimingReport = rule_test_case.sTimingReport

sRuleId = 's0_trace_001'

# The part has one pin, SDIN, clocked by SCLK.
# The port O_DAC_DATA is captured by the clock on port O_DAC_SCLK.
# These delays, with the passing part setup and hold, pass every stage 3 rule.
fMaxDelay = rule_test_case.fPassingMaxDelay
fMinDelay = rule_test_case.fPassingMinDelay


def create_trace(sName, sDevicePin, sPartPin, sDirection, fMaxDelay, fMinDelay):
    dTrace = {}
    dTrace['name'] = sName
    dTrace['device_pin'] = sDevicePin
    dTrace['part_pin'] = sPartPin
    dTrace['direction'] = sDirection
    dTrace['max_delay'] = fMaxDelay
    dTrace['min_delay'] = fMinDelay
    return dTrace


def create_data_trace(sDevicePin, sPartPin):
    # Each trace is named after its pins, as trace names are unique in a traces file.
    return create_trace(f'data_{sDevicePin}_{sPartPin}', sDevicePin, sPartPin, 'device_to_part', fMaxDelay, fMinDelay)


def create_clock_trace(sDevicePin, sPartPin):
    return create_trace(f'clock_{sDevicePin}_{sPartPin}', sDevicePin, sPartPin, 'device_to_part', fMaxDelay, fMinDelay)


def create_passing_data_trace():
    return create_data_trace('O_DAC_DATA', 'SDIN')


def create_passing_clock_trace():
    return create_clock_trace('O_DAC_SCLK', 'SCLK')


def create_passing_traces():
    lTraces = []
    lTraces.append(create_passing_data_trace())
    lTraces.append(create_passing_clock_trace())
    return lTraces


def build_config_text(sPartFile, sTracesFile):
    lText = []
    lText.append('description = "s0_trace_001 test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append('part_interface = "Serial Interface"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[clock]]')
    lText.append('name = "clk_100mhz"')
    lText.append('period = 10')
    lText.append('[[clock]]')
    lText.append('name = "dac_sclk"')
    lText.append('period = 40.0')
    lText.append('port = "O_DAC_SCLK"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 8}')
    lText.append('capture_clock = {name = "dac_sclk", setup_edge = "D", hold_edge = "B"}')
    lText.append('registers = ["q_spi_output_data_reg"]')
    lText.append(f'timing_reports = ["{sTimingReport}"]')
    # A deferred port with its own trace to SDIN, so every pin of the part has a port.
    # A broken trace of O_DAC_DATA is then found by this rule, rather than by traces_config_010 or interface_config_024.
    lText.append('[[port]]')
    lText.append('status = "defer"')
    lText.append('name = "O_SPARE_DATA"')
    return '\n'.join(lText)


def build_traces_text(lTraces):
    lText = []
    for dTrace in lTraces + [create_data_trace('O_SPARE_DATA', 'SDIN')]:
        lText.append('[[trace]]')
        lText.append(f'name = "{dTrace["name"]}"')
        lText.append(f'device_pin = "{dTrace["device_pin"]}"')
        lText.append(f'part_pin = "{dTrace["part_pin"]}"')
        lText.append(f'{dTrace["direction"]} = {{max_delay = {dTrace["max_delay"]}, min_delay = {dTrace["min_delay"]}}}')
    return '\n'.join(lText)


class Test(rule_test_case.RuleTestCase):

    def execute(self, lTraces):
        rule_test_case.write_file(self.sInterfaceFile, build_config_text(self.sPartFile, self.sTracesFile))
        rule_test_case.write_file(self.sPartFile, rule_test_case.build_passing_part_text())
        rule_test_case.write_file(self.sTracesFile, build_traces_text(lTraces))
        return self.run_check()

    def test_passes_when_data_trace_and_clock_trace_exist(self):
        self.execute(create_passing_traces())

        self.assert_rule_passed(sRuleId)

    def test_fails_when_no_trace_has_port_as_device_pin(self):
        lTraces = []
        lTraces.append(create_data_trace('O_OTHER_DATA', 'SDIN'))
        lTraces.append(create_passing_clock_trace())
        self.execute(lTraces)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_data_trace_part_pin_is_not_a_pin_of_the_part(self):
        lTraces = []
        lTraces.append(create_data_trace('O_DAC_DATA', 'SDO'))
        lTraces.append(create_passing_clock_trace())
        self.execute(lTraces)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_no_trace_has_capture_clock_port_as_device_pin(self):
        lTraces = []
        lTraces.append(create_passing_data_trace())
        lTraces.append(create_clock_trace('O_OTHER_SCLK', 'SCLK'))
        self.execute(lTraces)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_capture_clock_trace_part_pin_is_not_the_clock_pin(self):
        lTraces = []
        lTraces.append(create_passing_data_trace())
        lTraces.append(create_clock_trace('O_DAC_SCLK', 'CSF'))
        self.execute(lTraces)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_clock_device_pin_and_part_pin_match_on_different_traces(self):
        # Neither trace connects O_DAC_SCLK to SCLK
        lTraces = []
        lTraces.append(create_passing_data_trace())
        lTraces.append(create_clock_trace('O_DAC_SCLK', 'CSF'))
        lTraces.append(create_clock_trace('O_OTHER_SCLK', 'SCLK'))
        self.execute(lTraces)

        self.assert_rule_failed(sRuleId)

    def test_passes_when_another_clock_trace_to_the_clock_pin_is_listed_first(self):
        lTraces = []
        lTraces.append(create_passing_data_trace())
        lTraces.append(create_trace('other_clock', 'O_OTHER_SCLK', 'SCLK', 'device_to_part', 9.0, 9.0))
        lTraces.append(create_passing_clock_trace())
        self.execute(lTraces)

        self.assert_rule_passed(sRuleId)

    def test_stage_3_uses_clock_trace_from_capture_clock_port_when_another_is_listed_first(self):
        # With the 9.0 delay of O_OTHER_SCLK the maximum output delay would be 10 + 3.0 - 9.0 = 4.000
        lTraces = []
        lTraces.append(create_passing_data_trace())
        lTraces.append(create_trace('other_clock', 'O_OTHER_SCLK', 'SCLK', 'device_to_part', 9.0, 9.0))
        lTraces.append(create_passing_clock_trace())
        self.execute(lTraces)

        self.assertEqual([], list(self.find_testcase('s3_output_delay_001')))

    def test_fails_when_data_trace_has_no_device_to_part_delays(self):
        lTraces = []
        lTraces.append(create_trace('data_output', 'O_DAC_DATA', 'SDIN', 'part_to_device', fMaxDelay, fMinDelay))
        lTraces.append(create_passing_clock_trace())
        self.execute(lTraces)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_clock_trace_has_no_device_to_part_delays(self):
        lTraces = []
        lTraces.append(create_passing_data_trace())
        lTraces.append(create_trace('clock', 'O_DAC_SCLK', 'SCLK', 'part_to_device', fMaxDelay, fMinDelay))
        self.execute(lTraces)

        self.assert_rule_failed(sRuleId)

    def test_passes_when_unrelated_traces_exist(self):
        lTraces = []
        lTraces.append(create_data_trace('O_OTHER_DATA', 'SDO'))
        lTraces.append(create_clock_trace('O_DAC_CSF', 'CSF'))
        lTraces.extend(create_passing_traces())
        self.execute(lTraces)

        self.assert_rule_passed(sRuleId)

    def test_skips_stage_3_when_data_trace_is_missing(self):
        lTraces = []
        lTraces.append(create_passing_clock_trace())
        self.execute(lTraces)

        oSkipped = self.find_testcase('s3_output_delay_001').find('skipped')
        self.assertEqual('stage 0 failed', oSkipped.get('message'))

    def test_exit_code_is_one_when_data_trace_is_missing(self):
        lTraces = []
        lTraces.append(create_passing_clock_trace())
        iExitCode = self.execute(lTraces)

        self.assertEqual(1, iExitCode)
