from tests.rules import rule_test_case


# Every timing report in this file is launched by clk_100mhz with a period of 10.000ns
# and captured by dac_sclk with a period of 40.000ns.
sTimingReport = rule_test_case.sTimingReport

# Lines of the first timing report in sTimingReport, Max at Slow Process Corner
iFirstReportLaunchClockLine = rule_test_case.iLaunchClockLine
iFirstReportCaptureClockLine = rule_test_case.iCaptureClockLine

sPassingLaunchName = 'clk_100mhz'
fPassingLaunchPeriod = 10.0
sPassingCaptureName = 'dac_sclk'
fPassingCapturePeriod = 40.0


def build_config_text(sPartFile, sTracesFile, sTimingReportFile, oClocks):
    lText = []
    lText.append('description = "clock rule test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append('part_interface = "Serial Interface"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[clock]]')
    lText.append(f'name = "{oClocks.launch_name}"')
    lText.append(f'period = {oClocks.launch_period}')
    lText.append('[[clock]]')
    lText.append(f'name = "{oClocks.capture_name}"')
    lText.append(f'period = {oClocks.capture_period}')
    lText.append('port = "O_DAC_SCLK"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append(f'launch_clock = {{name = "{oClocks.launch_name}", setup_edge = 8, hold_edge = 8}}')
    lText.append(f'capture_clock = {{name = "{oClocks.capture_name}", setup_edge = "D", hold_edge = "B"}}')
    lText.append(f'timing_reports = ["{sTimingReportFile}"]')
    return '\n'.join(lText)


class Clocks():

    def __init__(self, sLaunchName, fLaunchPeriod, sCaptureName, fCapturePeriod):
        self.launch_name = sLaunchName
        self.launch_period = fLaunchPeriod
        self.capture_name = sCaptureName
        self.capture_period = fCapturePeriod


class ClockRuleTestCase(rule_test_case.RuleTestCase):

    def execute_with_launch_clock(self, sName, fPeriod):
        oClocks = Clocks(sName, fPeriod, sPassingCaptureName, fPassingCapturePeriod)
        return self.execute(oClocks, sTimingReport)

    def execute_with_capture_clock(self, sName, fPeriod):
        oClocks = Clocks(sPassingLaunchName, fPassingLaunchPeriod, sName, fPeriod)
        return self.execute(oClocks, sTimingReport)

    def execute_with_first_report_line_changed(self, iLineNumber, sOld, sNew):
        lLines = rule_test_case.read_lines(sTimingReport)
        self.assertIn(sOld, lLines[iLineNumber - 1])
        lLines[iLineNumber - 1] = lLines[iLineNumber - 1].replace(sOld, sNew)
        rule_test_case.write_file(self.sChangedTimingReport, '\n'.join(lLines))
        oClocks = Clocks(sPassingLaunchName, fPassingLaunchPeriod, sPassingCaptureName, fPassingCapturePeriod)
        return self.execute(oClocks, self.sChangedTimingReport)

    def execute(self, oClocks, sTimingReportFile):
        rule_test_case.write_file(self.sInterfaceFile, build_config_text(self.sPartFile, self.sTracesFile, sTimingReportFile, oClocks))
        rule_test_case.write_file(self.sPartFile, rule_test_case.build_passing_part_text())
        rule_test_case.write_file(self.sTracesFile, rule_test_case.build_passing_traces_text())
        return self.run_check()
