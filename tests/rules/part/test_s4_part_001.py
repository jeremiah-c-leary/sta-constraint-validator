import argparse
import contextlib
import datetime
import io
import os
import tempfile
import unittest
import xml.etree.ElementTree

from stacv.cli import check

sTestDir = os.path.dirname(os.path.abspath(__file__))
sParseDir = os.path.join(sTestDir, '..', '..', 'timing_report', 'parse', 'vivado')

# Every timing report in this file times the rising edge of the capture clock dac_sclk.
# The requirements are on lines 21, 82, 165 and 226.
sTimingReport = os.path.abspath(os.path.join(sParseDir, 'O_DAC_DATA_timing.rpt'))
lRequirementLines = [21, 82, 165, 226]

sSuiteName = 'O_DAC_DATA.SDR-SS-O'
sRuleId = 's4_part_001'


def build_config_text(sPartFile, sTracesFile, sTimingReportFile):
    lText = []
    lText.append('description = "s4_part_001 test"')
    lText.append('interface = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append('launch_clock = {name = "clk_100mhz", period = 10.000, setup_edge = 8, hold_edge = 0}')
    lText.append('capture_clock = {port = "O_DAC_SCLK", name = "dac_sclk", period = 50, setup_edge = "C", hold_edge = "A"}')
    lText.append(f'timing_reports = ["{sTimingReportFile}"]')
    return '\n'.join(lText)


def build_part_text(sCaptureEdge):
    # With the traces below, the calculated output delays match sTimingReport:
    #    maximum:   0.5 + 2.0 - 0.5 = 2.000
    #    minimum:  -0.5 + 2.0 - 0.5 = 1.000
    lText = []
    lText.append('[properties]')
    lText.append('manufacturer = "Texas Instruments"')
    lText.append('part_number = "DAC81404"')
    lText.append('[datasheet]')
    lText.append('name = "DACx1401 Quad, 16-Bit and 12-Bit, High-Voltage-Output DACs With Internal Reference"')
    lText.append('url = "https://www.ti.com/lit/ds/symlink/dac81404.pdf"')
    lText.append('version = "SLASEH2A -- November 2020 -- REVISED MAY 2021"')
    lText.append('[[interface]]')
    lText.append('name = "Serial Interface"')
    lText.append('[[interface.pin]]')
    lText.append('name = "SDIN"')
    lText.append('methodology = "SDR-SS-I"')
    lText.append('clock = {pin = "SCLK", max_frequency = 25}')
    lText.append(f'capture_edge = "{sCaptureEdge}"')
    lText.append('setup = {value = 0.5, symbol = "tSDIS", source = "Table 7.6"}')
    lText.append('hold = {value = 0.5, symbol = "tSDIH", source = "Table 7.6"}')
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


def read_lines(sFilename):
    with open(sFilename) as oFile:
        return oFile.read().split('\n')


def write_file(sFilename, sText):
    with open(sFilename, 'w') as oFile:
        oFile.write(sText)


class Test(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sConfigFile = os.path.join(self.oTempDir.name, 'stacv.toml')
        self.sPartFile = os.path.join(self.oTempDir.name, 'part.toml')
        self.sTracesFile = os.path.join(self.oTempDir.name, 'traces.toml')
        self.sChangedTimingReport = os.path.join(self.oTempDir.name, 'O_DAC_DATA_timing.rpt')
        self.sJunitFile = os.path.join(self.oTempDir.name, 'stacv_junit.xml')

    def tearDown(self):
        self.oTempDir.cleanup()

    def execute(self, sCaptureEdge, sTimingReportFile):
        write_file(self.sConfigFile, build_config_text(self.sPartFile, self.sTracesFile, sTimingReportFile))
        write_file(self.sPartFile, build_part_text(sCaptureEdge))
        write_file(self.sTracesFile, build_traces_text())
        oArgs = argparse.Namespace(config_file=self.sConfigFile, report=None, junit=self.sJunitFile)
        oDateTime = datetime.datetime(2026, 10, 24, 20, 0, 0)
        lArgv = ['stacv', 'check', self.sConfigFile, '--junit', self.sJunitFile]
        with contextlib.redirect_stdout(io.StringIO()):
            return check.execute(oArgs, oDateTime, lArgv)

    def execute_with_requirement_lines_changed(self, sCaptureEdge, lLineNumbers):
        lLines = read_lines(sTimingReport)
        for iLineNumber in lLineNumbers:
            self.assertIn('dac_sclk rise@', lLines[iLineNumber - 1])
            lLines[iLineNumber - 1] = lLines[iLineNumber - 1].replace('dac_sclk rise@', 'dac_sclk fall@')
        write_file(self.sChangedTimingReport, '\n'.join(lLines))
        return self.execute(sCaptureEdge, self.sChangedTimingReport)

    def find_rule_testcase(self):
        oRoot = xml.etree.ElementTree.parse(self.sJunitFile).getroot()
        for oSuite in oRoot.findall('testsuite'):
            if oSuite.get('name') == sSuiteName:
                for oTestcase in oSuite.findall('testcase'):
                    if oTestcase.get('name') == sRuleId:
                        return oTestcase
        raise ValueError(f'{sSuiteName} {sRuleId} is not in the JUnit file')

    def assert_rule_passed(self):
        oTestcase = self.find_rule_testcase()
        self.assertEqual([], list(oTestcase))

    def assert_rule_failed(self):
        oTestcase = self.find_rule_testcase()
        self.assertIsNotNone(oTestcase.find('failure'))

    def test_passes_when_part_captures_on_rising_edge_and_reports_time_rising_edge(self):
        self.execute('Rising', sTimingReport)

        self.assert_rule_passed()

    def test_exit_code_is_zero_when_capture_clock_edge_type_matches(self):
        iExitCode = self.execute('Rising', sTimingReport)

        self.assertEqual(0, iExitCode)

    def test_fails_when_part_captures_on_falling_edge_and_reports_time_rising_edge(self):
        self.execute('Falling', sTimingReport)

        self.assert_rule_failed()

    def test_exit_code_is_one_when_capture_clock_edge_type_differs(self):
        iExitCode = self.execute('Falling', sTimingReport)

        self.assertEqual(1, iExitCode)

    def test_passes_when_part_captures_on_falling_edge_and_reports_time_falling_edge(self):
        self.execute_with_requirement_lines_changed('Falling', lRequirementLines)

        self.assert_rule_passed()

    def test_fails_when_part_captures_on_rising_edge_and_reports_time_falling_edge(self):
        self.execute_with_requirement_lines_changed('Rising', lRequirementLines)

        self.assert_rule_failed()

    def test_fails_when_one_timing_report_times_a_different_edge_type(self):
        self.execute_with_requirement_lines_changed('Rising', [226])

        self.assert_rule_failed()

    def test_failure_lists_each_timing_report_with_a_different_edge_type(self):
        self.execute('Falling', sTimingReport)

        lExpected = []
        for iLineNumber in lRequirementLines:
            lExpected.append(f'{sTimingReport}:{iLineNumber}  capture clock edge rise, part SDIN captures on Falling')
        oFailure = self.find_rule_testcase().find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)

    def test_failure_lists_only_the_timing_report_with_a_different_edge_type(self):
        self.execute_with_requirement_lines_changed('Rising', [226])

        lExpected = []
        lExpected.append(f'{self.sChangedTimingReport}:226  capture clock edge fall, part SDIN captures on Rising')
        oFailure = self.find_rule_testcase().find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)
