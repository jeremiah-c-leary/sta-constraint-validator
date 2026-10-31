import os

from tests.rules import rule_test_case

sTestDir = os.path.dirname(os.path.abspath(__file__))
sParseDir = os.path.join(sTestDir, '..', '..', 'timing_report', 'parse', 'vivado')

# The data path of every timing report in this file ends at O_DAC_DATA.
# The last element of each data path is on lines 47, 113, 191 and 257.
# Lines 47 and 191 are in hold timing reports, lines 113 and 257 in setup timing reports.
sTimingReport = os.path.abspath(os.path.join(sParseDir, 'O_DAC_DATA_timing.rpt'))
lDataPathEndLines = [47, 113, 191, 257]

sRuleId = 's0_data_path_001'

sPassingPortName = 'O_DAC_DATA'


def build_config_text(sPartFile, sTracesFile, sTimingReportFile, sPortName):
    lText = []
    lText.append('description = "s0_data_path_001 test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[clock]]')
    lText.append('name = "clk_100mhz"')
    lText.append('period = 10.000')
    lText.append('[[clock]]')
    lText.append('name = "dac_sclk"')
    lText.append('period = 50.0')
    lText.append('port = "O_DAC_SCLK"')
    lText.append('[[port]]')
    lText.append(f'name = "{sPortName}"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
    lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
    lText.append(f'timing_reports = ["{sTimingReportFile}"]')
    return '\n'.join(lText)


class Test(rule_test_case.RuleTestCase):

    def execute_with_port_name(self, sPortName):
        return self.execute(sPortName, sTimingReport)

    def execute_with_data_path_ends_changed(self, lLineNumbers, sNewPortName):
        lLines = rule_test_case.read_lines(sTimingReport)
        for iLineNumber in lLineNumbers:
            self.assertIn('O_DAC_DATA', lLines[iLineNumber - 1])
            lLines[iLineNumber - 1] = lLines[iLineNumber - 1].replace('O_DAC_DATA', sNewPortName)
        rule_test_case.write_file(self.sChangedTimingReport, '\n'.join(lLines))
        return self.execute(sPassingPortName, self.sChangedTimingReport)

    def execute(self, sPortName, sTimingReportFile):
        self.sSuiteName = f'{sPortName}.SDR-SS-O'
        rule_test_case.write_file(self.sInterfaceFile, build_config_text(self.sPartFile, self.sTracesFile, sTimingReportFile, sPortName))
        rule_test_case.write_file(self.sPartFile, rule_test_case.build_passing_part_text())
        rule_test_case.write_file(self.sTracesFile, rule_test_case.build_passing_traces_text())
        return self.run_check()

    def test_passes_when_data_path_ends_at_configured_port(self):
        self.execute_with_port_name(sPassingPortName)

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_data_path_ends_at_configured_port(self):
        iExitCode = self.execute_with_port_name(sPassingPortName)

        self.assertEqual(0, iExitCode)

    def test_fails_when_configured_port_differs(self):
        self.execute_with_port_name('O_DAC_CSF')

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_data_path_ends_elsewhere(self):
        # Every data path still has the same elements, so only this rule fails.
        iExitCode = self.execute_with_data_path_ends_changed(lDataPathEndLines, 'O_DAC_OTHER')

        self.assertEqual(1, iExitCode)

    def test_fails_when_data_path_of_one_setup_timing_report_ends_elsewhere(self):
        self.execute_with_data_path_ends_changed([257], 'O_DAC_OTHER')

        self.assert_rule_failed(sRuleId)

    def test_fails_when_data_path_of_one_hold_timing_report_ends_elsewhere(self):
        self.execute_with_data_path_ends_changed([47], 'O_DAC_OTHER')

        self.assert_rule_failed(sRuleId)

    def test_skips_stage_3_when_data_path_ends_elsewhere(self):
        # Every data path still has the same elements, so only this rule fails.
        self.execute_with_data_path_ends_changed(lDataPathEndLines, 'O_DAC_OTHER')

        oSkipped = self.find_testcase('s3_output_delay_001').find('skipped')
        self.assertEqual('stage 0 failed', oSkipped.get('message'))

    def test_failure_lists_each_timing_report_whose_data_path_ends_elsewhere(self):
        self.execute_with_port_name('O_DAC_CSF')

        lExpected = []
        for iLineNumber in lDataPathEndLines:
            lExpected.append(f'{sTimingReport}:{iLineNumber}  data path ends at O_DAC_DATA, configured port O_DAC_CSF')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)

    def test_failure_lists_only_the_timing_report_whose_data_path_ends_elsewhere(self):
        self.execute_with_data_path_ends_changed([257], 'O_DAC_OTHER')

        lExpected = []
        lExpected.append(f'{self.sChangedTimingReport}:257  data path ends at O_DAC_OTHER, configured port O_DAC_DATA')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)
