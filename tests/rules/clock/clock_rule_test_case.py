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

# Every timing report in this file is launched by clk_100mhz with a period of 10.000ns
# and captured by dac_sclk with a period of 50.000ns.
sTimingReport = os.path.abspath(os.path.join(sParseDir, 'O_DAC_DATA_timing.rpt'))

# Lines of the last timing report in sTimingReport, Max at Slow Process Corner
iLastReportLaunchClockLine = 221
iLastReportCaptureClockLine = 223

sSuiteName = 'O_DAC_DATA.SDR-SS-O'

sPassingLaunchName = 'clk_100mhz'
fPassingLaunchFrequency = 100
sPassingCaptureName = 'dac_sclk'
fPassingCaptureFrequency = 20


def build_config_text(sPartFile, sTracesFile, sTimingReportFile, oClocks):
    lText = []
    lText.append('description = "clock rule test"')
    lText.append('interface = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append(f'launch_clock = {{name = "{oClocks.launch_name}", period = {oClocks.launch_frequency}}}')
    lText.append(f'capture_clock = {{port = "O_DAC_SCLK", name = "{oClocks.capture_name}", period = {oClocks.capture_frequency}}}')
    lText.append(f'timing_reports = ["{sTimingReportFile}"]')
    return '\n'.join(lText)


def build_part_text():
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
    lText.append('capture_edge = "Falling"')
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


class Clocks():

    def __init__(self, sLaunchName, fLaunchFrequency, sCaptureName, fCaptureFrequency):
        self.launch_name = sLaunchName
        self.launch_frequency = fLaunchFrequency
        self.capture_name = sCaptureName
        self.capture_frequency = fCaptureFrequency


class ClockRuleTestCase(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sConfigFile = os.path.join(self.oTempDir.name, 'stacv.toml')
        self.sPartFile = os.path.join(self.oTempDir.name, 'part.toml')
        self.sTracesFile = os.path.join(self.oTempDir.name, 'traces.toml')
        self.sChangedTimingReport = os.path.join(self.oTempDir.name, 'O_DAC_DATA_timing.rpt')
        self.sJunitFile = os.path.join(self.oTempDir.name, 'stacv_junit.xml')

    def tearDown(self):
        self.oTempDir.cleanup()

    def execute_with_launch_clock(self, sName, fFrequency):
        oClocks = Clocks(sName, fFrequency, sPassingCaptureName, fPassingCaptureFrequency)
        return self.execute(oClocks, sTimingReport)

    def execute_with_capture_clock(self, sName, fFrequency):
        oClocks = Clocks(sPassingLaunchName, fPassingLaunchFrequency, sName, fFrequency)
        return self.execute(oClocks, sTimingReport)

    def execute_with_last_report_line_changed(self, iLineNumber, sOld, sNew):
        lLines = read_lines(sTimingReport)
        self.assertIn(sOld, lLines[iLineNumber - 1])
        lLines[iLineNumber - 1] = lLines[iLineNumber - 1].replace(sOld, sNew)
        write_file(self.sChangedTimingReport, '\n'.join(lLines))
        oClocks = Clocks(sPassingLaunchName, fPassingLaunchFrequency, sPassingCaptureName, fPassingCaptureFrequency)
        return self.execute(oClocks, self.sChangedTimingReport)

    def execute(self, oClocks, sTimingReportFile):
        write_file(self.sConfigFile, build_config_text(self.sPartFile, self.sTracesFile, sTimingReportFile, oClocks))
        write_file(self.sPartFile, build_part_text())
        write_file(self.sTracesFile, build_traces_text())
        oArgs = argparse.Namespace(config_file=self.sConfigFile, report=None, junit=self.sJunitFile)
        oDateTime = datetime.datetime(2026, 10, 22, 20, 0, 0)
        lArgv = ['stacv', 'check', self.sConfigFile, '--junit', self.sJunitFile]
        with contextlib.redirect_stdout(io.StringIO()):
            return check.execute(oArgs, oDateTime, lArgv)

    def find_testcase(self, sTestcaseName):
        oRoot = xml.etree.ElementTree.parse(self.sJunitFile).getroot()
        for oSuite in oRoot.findall('testsuite'):
            if oSuite.get('name') == sSuiteName:
                for oTestcase in oSuite.findall('testcase'):
                    if oTestcase.get('name') == sTestcaseName:
                        return oTestcase
        raise ValueError(f'{sSuiteName} {sTestcaseName} is not in the JUnit file')

    def assert_rule_passed(self, sRuleId):
        oTestcase = self.find_testcase(sRuleId)
        self.assertEqual([], list(oTestcase))

    def assert_rule_failed(self, sRuleId):
        oTestcase = self.find_testcase(sRuleId)
        self.assertIsNotNone(oTestcase.find('failure'))
