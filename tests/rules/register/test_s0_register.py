from stacv.interface import interface_config_error
from tests.rules import rule_test_case

# Every path in this file starts at q_spi_output_data_reg; the slack of each report is on lines 14, 91, 168 and 245.
sTimingReport = rule_test_case.sTimingReport
lSlackLines = rule_test_case.build_all_lines(rule_test_case.iSlackLine)


def build_config_text(sPartFile, sTracesFile, sRegisters):
    lText = []
    lText.append('description = "register rule test"')
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
    lText.append('capture_clock = {name = "dac_sclk", setup_edge = "D", hold_edge = "B"}')
    if sRegisters is not None:
        lText.append(f'registers = {sRegisters}')
    lText.append(f'timing_reports = ["{sTimingReport}"]')
    return '\n'.join(lText)


class RegisterTestCase(rule_test_case.RuleTestCase):

    def execute(self, sRegisters):
        rule_test_case.write_file(self.sInterfaceFile, build_config_text(self.sPartFile, self.sTracesFile, sRegisters))
        rule_test_case.write_file(self.sPartFile, rule_test_case.build_passing_part_text())
        rule_test_case.write_file(self.sTracesFile, rule_test_case.build_passing_traces_text())
        return self.run_check()


class TestListedRegisters(RegisterTestCase):

    sRuleId = 's0_register_001'

    def test_passes_when_every_register_is_listed(self):
        self.assertEqual(0, self.execute('["q_spi_output_data_reg"]'))
        self.assert_rule_passed(self.sRuleId)

    def test_passes_when_a_wildcard_matches_the_register(self):
        self.execute('["q_spi_output_*"]')
        self.assert_rule_passed(self.sRuleId)

    def test_a_port_without_registers_is_an_interface_error(self):
        with self.assertRaises(interface_config_error.InterfaceConfigError) as oContext:
            self.execute(None)
        self.assertIn('[interface_config_002]', str(oContext.exception))
        self.assertIn('missing required key "registers" in port O_DAC_DATA', str(oContext.exception))

    def test_fails_when_a_register_in_the_reports_is_not_listed(self):
        self.assertEqual(1, self.execute('["q_spi_other_reg"]'))
        lExpected = []
        for iLineNumber in lSlackLines:
            lExpected.append(f'{sTimingReport}:{iLineNumber}  register q_spi_output_data_reg is not in registers of O_DAC_DATA')
        self.assertEqual('\n'.join(lExpected), self.find_testcase(self.sRuleId).find('failure').text)


class TestReportedRegisters(RegisterTestCase):

    sRuleId = 's0_register_002'

    def test_passes_when_every_listed_register_is_reported(self):
        self.execute('["q_spi_output_data_reg"]')
        self.assert_rule_passed(self.sRuleId)

    def test_fails_when_a_listed_register_is_in_no_report(self):
        self.execute('["q_spi_output_data_reg", "q_spi_extra_reg"]')
        self.assertEqual('register q_spi_extra_reg of O_DAC_DATA is in no timing report', self.find_testcase(self.sRuleId).find('failure').text)


class TestPathLimit(RegisterTestCase):

    def test_passes_when_no_report_reaches_the_path_limit(self):
        self.execute('["q_spi_output_data_reg"]')
        self.assert_rule_passed('s0_register_003')
