from tests.rules import rule_test_case

# The capture clock path of every timing report in this file ends at O_DAC_SCLK.
# The last element of each capture clock path, the net to the clock port, is on lines 64, 141, 218 and 295.
# Lines 64 and 218 are in setup timing reports, lines 141 and 295 in hold timing reports.
sTimingReport = rule_test_case.sTimingReport
lCaptureClockPathEndLines = rule_test_case.build_all_lines(rule_test_case.iCaptureClockPathEndLine)
iSetupClockPathEndLine = lCaptureClockPathEndLines[0]
iHoldClockPathEndLine = lCaptureClockPathEndLines[1]

sRuleId = 's0_clock_path_001'

sPassingClockPortName = 'O_DAC_SCLK'


def build_config_text(sPartFile, sTracesFile, sTimingReportFile, sClockPortName):
    lText = []
    lText.append('description = "s0_clock_path_001 test"')
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
    lText.append(f'port = "{sClockPortName}"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 8}')
    lText.append(f'capture_clock = {{name = "dac_sclk", setup_edge = "D", hold_edge = "B"}}')
    lText.append('registers = ["q_spi_output_data_reg"]')
    lText.append(f'timing_reports = ["{sTimingReportFile}"]')
    return '\n'.join(lText)


class Test(rule_test_case.RuleTestCase):

    def execute_with_clock_port_name(self, sClockPortName):
        return self.execute(sClockPortName, sTimingReport)

    def execute_with_capture_clock_path_ends_changed(self, lLineNumbers, sNewClockPortName):
        lLines = rule_test_case.read_lines(sTimingReport)
        for iLineNumber in lLineNumbers:
            self.assertIn('O_DAC_SCLK', lLines[iLineNumber - 1])
            lLines[iLineNumber - 1] = lLines[iLineNumber - 1].replace('O_DAC_SCLK', sNewClockPortName)
        rule_test_case.write_file(self.sChangedTimingReport, '\n'.join(lLines))
        return self.execute(sPassingClockPortName, self.sChangedTimingReport)

    def execute(self, sClockPortName, sTimingReportFile):
        rule_test_case.write_file(self.sInterfaceFile, build_config_text(self.sPartFile, self.sTracesFile, sTimingReportFile, sClockPortName))
        rule_test_case.write_file(self.sPartFile, rule_test_case.build_passing_part_text())
        rule_test_case.write_file(self.sTracesFile, rule_test_case.build_passing_traces_text())
        return self.run_check()

    def test_passes_when_capture_clock_path_ends_at_configured_clock_port(self):
        self.execute_with_clock_port_name(sPassingClockPortName)

        self.assert_rule_passed(sRuleId)

    def test_exit_code_is_zero_when_capture_clock_path_ends_at_configured_clock_port(self):
        iExitCode = self.execute_with_clock_port_name(sPassingClockPortName)

        self.assertEqual(0, iExitCode)

    def test_fails_when_configured_clock_port_differs(self):
        self.execute_with_clock_port_name('O_DAC_CSF')

        self.assert_rule_failed(sRuleId)

    def test_exit_code_is_one_when_capture_clock_path_ends_elsewhere(self):
        # Every capture clock path still has the same elements, so only this rule fails.
        iExitCode = self.execute_with_capture_clock_path_ends_changed(lCaptureClockPathEndLines, 'O_DAC_OTHER')

        self.assertEqual(1, iExitCode)

    def test_fails_when_capture_clock_path_of_one_setup_timing_report_ends_elsewhere(self):
        self.execute_with_capture_clock_path_ends_changed([iSetupClockPathEndLine], 'O_DAC_OTHER')

        self.assert_rule_failed(sRuleId)

    def test_fails_when_capture_clock_path_of_one_hold_timing_report_ends_elsewhere(self):
        self.execute_with_capture_clock_path_ends_changed([iHoldClockPathEndLine], 'O_DAC_OTHER')

        self.assert_rule_failed(sRuleId)

    def test_skips_stage_3_when_capture_clock_path_ends_elsewhere(self):
        # Every capture clock path still has the same elements, so only this rule fails.
        self.execute_with_capture_clock_path_ends_changed(lCaptureClockPathEndLines, 'O_DAC_OTHER')

        oSkipped = self.find_testcase('s3_output_delay_001').find('skipped')
        self.assertEqual('stage 0 failed', oSkipped.get('message'))

    def test_failure_lists_each_timing_report_whose_capture_clock_path_ends_elsewhere(self):
        self.execute_with_clock_port_name('O_DAC_CSF')

        lExpected = []
        for iLineNumber in lCaptureClockPathEndLines:
            lExpected.append(f'{sTimingReport}:{iLineNumber}  capture clock path ends at O_DAC_SCLK, configured clock port O_DAC_CSF')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)

    def test_failure_lists_only_the_timing_report_whose_capture_clock_path_ends_elsewhere(self):
        self.execute_with_capture_clock_path_ends_changed([iSetupClockPathEndLine], 'O_DAC_OTHER')

        lExpected = []
        lExpected.append(f'{self.sChangedTimingReport}:{iSetupClockPathEndLine}  capture clock path ends at O_DAC_OTHER, configured clock port O_DAC_SCLK')
        oFailure = self.find_testcase(sRuleId).find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)
