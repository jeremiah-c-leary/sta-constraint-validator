import os

from tests.rules import rule_test_case

sTestDir = os.path.dirname(os.path.abspath(__file__))
sParseDir = os.path.join(sTestDir, '..', '..', 'timing_report', 'parse', 'vivado')

# Every timing report in this file is launched by clk_100mhz with a period of 10.000ns
# and captured by dac_sclk with a period of 50.000ns.
sTimingReport = os.path.abspath(os.path.join(sParseDir, 'O_DAC_DATA_timing.rpt'))

# Lines of the last timing report in sTimingReport, Max at Slow Process Corner
iLastReportLaunchClockLine = 221
iLastReportCaptureClockLine = 223

sPassingLaunchName = 'clk_100mhz'
fPassingLaunchPeriod = 10.0
sPassingCaptureName = 'dac_sclk'
fPassingCapturePeriod = 50.0


def build_config_text(sPartFile, sTracesFile, sTimingReportFile, oClocks):
    lText = []
    lText.append('description = "clock rule test"')
    lText.append('interface = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append(f'launch_clock = {{name = "{oClocks.launch_name}", period = {oClocks.launch_period}, setup_edge = 8, hold_edge = 0}}')
    lText.append(f'capture_clock = {{port = "O_DAC_SCLK", name = "{oClocks.capture_name}", period = {oClocks.capture_period}, setup_edge = "C", hold_edge = "A"}}')
    lText.append(f'timing_reports = ["{sTimingReportFile}"]')
    return '\n'.join(lText)


def build_traces_text():
    lText = []
    lText.append('[[trace]]')
    lText.append('name = "data_output"')
    lText.append('device_pin = "O_DAC_DATA"')
    lText.append('part_pin = "SDIN"')
    lText.append('device_to_part = {max_delay = 2.0, min_delay = 2.0}')
    lText.append('[[trace]]')
    lText.append('name = "clock"')
    lText.append('device_pin = "O_DAC_SCLK"')
    lText.append('part_pin = "SCLK"')
    lText.append('device_to_part = {max_delay = 0.5, min_delay = 0.5}')
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

    def execute_with_last_report_line_changed(self, iLineNumber, sOld, sNew):
        lLines = rule_test_case.read_lines(sTimingReport)
        self.assertIn(sOld, lLines[iLineNumber - 1])
        lLines[iLineNumber - 1] = lLines[iLineNumber - 1].replace(sOld, sNew)
        rule_test_case.write_file(self.sChangedTimingReport, '\n'.join(lLines))
        oClocks = Clocks(sPassingLaunchName, fPassingLaunchPeriod, sPassingCaptureName, fPassingCapturePeriod)
        return self.execute(oClocks, self.sChangedTimingReport)

    def execute(self, oClocks, sTimingReportFile):
        rule_test_case.write_file(self.sConfigFile, build_config_text(self.sPartFile, self.sTracesFile, sTimingReportFile, oClocks))
        rule_test_case.write_file(self.sPartFile, rule_test_case.build_passing_part_text())
        rule_test_case.write_file(self.sTracesFile, build_traces_text())
        return self.run_check()
