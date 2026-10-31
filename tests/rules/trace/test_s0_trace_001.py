import os

from tests.rules import rule_test_case

sTestDir = os.path.dirname(os.path.abspath(__file__))
sParseDir = os.path.join(sTestDir, '..', '..', 'timing_report', 'parse', 'vivado')

# Setup reports at both process corners have an output delay of 2.000ns.
# Hold reports at both process corners have an output delay of 1.000ns.
sTimingReport = os.path.abspath(os.path.join(sParseDir, 'O_DAC_DATA_timing.rpt'))

sRuleId = 's0_trace_001'

# The part has one pin, SDIN, clocked by SCLK.
# The port O_DAC_DATA is captured by the clock on port O_DAC_SCLK.
# These delays, with a part setup and hold of 0.5, pass every stage 3 rule.
fDataDelay = 2.0
fClockDelay = 0.5


def create_trace(sName, sDevicePin, sPartPin, sDirection, fDelay):
    dTrace = {}
    dTrace['name'] = sName
    dTrace['device_pin'] = sDevicePin
    dTrace['part_pin'] = sPartPin
    dTrace['direction'] = sDirection
    dTrace['delay'] = fDelay
    return dTrace


def create_data_trace(sDevicePin, sPartPin):
    return create_trace('data_output', sDevicePin, sPartPin, 'device_to_part', fDataDelay)


def create_clock_trace(sDevicePin, sPartPin):
    return create_trace('clock', sDevicePin, sPartPin, 'device_to_part', fClockDelay)


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
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[clock]]')
    lText.append('name = "clk_100mhz"')
    lText.append('period = 10')
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
        lText.append(f'{dTrace["direction"]} = {{max_delay = {dTrace["delay"]}, min_delay = {dTrace["delay"]}}}')
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
        lTraces.append(create_trace('other_clock', 'O_OTHER_SCLK', 'SCLK', 'device_to_part', 9.0))
        lTraces.append(create_passing_clock_trace())
        self.execute(lTraces)

        self.assert_rule_passed(sRuleId)

    def test_stage_3_uses_clock_trace_from_capture_clock_port_when_another_is_listed_first(self):
        # With the 9.0 delay of O_OTHER_SCLK the maximum output delay would be 0.5 + 2.0 - 9.0 = -6.500
        lTraces = []
        lTraces.append(create_passing_data_trace())
        lTraces.append(create_trace('other_clock', 'O_OTHER_SCLK', 'SCLK', 'device_to_part', 9.0))
        lTraces.append(create_passing_clock_trace())
        self.execute(lTraces)

        self.assertEqual([], list(self.find_testcase('s3_output_delay_001')))

    def test_fails_when_data_trace_has_no_device_to_part_delays(self):
        lTraces = []
        lTraces.append(create_trace('data_output', 'O_DAC_DATA', 'SDIN', 'part_to_device', fDataDelay))
        lTraces.append(create_passing_clock_trace())
        self.execute(lTraces)

        self.assert_rule_failed(sRuleId)

    def test_fails_when_clock_trace_has_no_device_to_part_delays(self):
        lTraces = []
        lTraces.append(create_passing_data_trace())
        lTraces.append(create_trace('clock', 'O_DAC_SCLK', 'SCLK', 'part_to_device', fClockDelay))
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
