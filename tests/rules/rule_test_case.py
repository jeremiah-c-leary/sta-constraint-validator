import argparse
import contextlib
import datetime
import io
import os
import tempfile
import unittest
import xml.etree.ElementTree

from stacv.cli import check

sSuiteName = 'O_DAC_DATA.SDR-SS-O'

# The rule tests check the DAC81404 example: its timing report is a Vivado run of the constraints stacv generates for it.
sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sExampleDir = os.path.join(sProjectDir, 'example', 'texas_instruments', 'DAC81404')
sTimingReport = os.path.join(sExampleDir, 'timing_reports', 'O_DAC_DATA_timing.rpt')

# The example's clocks and edges.
fLaunchPeriod = 10.0
fCapturePeriod = 40.0
iLaunchEdge = 8
sCaptureSetupEdge = 'D'
sCaptureHoldEdge = 'B'

# The timing report holds four reports, each 77 lines long, in this order:
#    setup at the Slow Process Corner
#    hold at the Slow Process Corner
#    setup at the Fast Process Corner
#    hold at the Fast Process Corner
iReportLength = 77
lSetupReportOffsets = [0, 2 * iReportLength]
lHoldReportOffsets = [iReportLength, 3 * iReportLength]

# Lines of the first report, the setup report at the Slow Process Corner.
iSlackLine = 14
iLaunchClockLine = 16
iCaptureClockLine = 18
iRequirementLine = 21
iOutputDelayLine = 24
iDataPathEndLine = 50
iCaptureClockPathEndLine = 64


def build_lines(iLine, lOffsets):
    lLines = []
    for iOffset in lOffsets:
        lLines.append(iLine + iOffset)
    return lLines


def build_setup_lines(iLine):
    return build_lines(iLine, lSetupReportOffsets)


def build_hold_lines(iLine):
    return build_lines(iLine, lHoldReportOffsets)


def build_all_lines(iLine):
    return sorted(build_setup_lines(iLine) + build_hold_lines(iLine))


# With the passing part and traces, the calculated output delays match the timing report:
#    maximum:   setup + data max_delay - clock min_delay =  10 + 3.0 - 1.0 =  12.000
#    minimum:  -hold  + data min_delay - clock max_delay = -10 + 1.0 - 3.0 = -12.000
sPassingCaptureEdge = 'Falling'
fPassingSetup = 10.0
fPassingHold = 10.0
fPassingMaxDelay = 3.0
fPassingMinDelay = 1.0


def build_passing_part_text():
    return build_part_text(sPassingCaptureEdge, fPassingSetup, fPassingHold)


def build_part_text(sCaptureEdge, fSetup, fHold):
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
    lText.append(f'setup = {{value = {fSetup}, symbol = "tSDIS", source = "Table 7.6"}}')
    lText.append(f'hold = {{value = {fHold}, symbol = "tSDIH", source = "Table 7.6"}}')
    return '\n'.join(lText)


def build_passing_traces_text():
    lText = []
    lText.append('[[trace]]')
    lText.append('name = "data_output"')
    lText.append('device_pin = "O_DAC_DATA"')
    lText.append('part_pin = "SDIN"')
    lText.append(f'device_to_part = {{max_delay = {fPassingMaxDelay}, min_delay = {fPassingMinDelay}}}')
    lText.append('[[trace]]')
    lText.append('name = "clock"')
    lText.append('device_pin = "O_DAC_SCLK"')
    lText.append('part_pin = "SCLK"')
    lText.append(f'device_to_part = {{max_delay = {fPassingMaxDelay}, min_delay = {fPassingMinDelay}}}')
    return '\n'.join(lText)


def read_lines(sFilename):
    with open(sFilename) as oFile:
        return oFile.read().split('\n')


def write_file(sFilename, sText):
    with open(sFilename, 'w') as oFile:
        oFile.write(sText)


class RuleTestCase(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sInterfaceFile = os.path.join(self.oTempDir.name, 'interface.toml')
        self.sPartFile = os.path.join(self.oTempDir.name, 'part.toml')
        self.sTracesFile = os.path.join(self.oTempDir.name, 'traces.toml')
        self.sChangedTimingReport = os.path.join(self.oTempDir.name, 'O_DAC_DATA_timing.rpt')
        self.sJunitFile = os.path.join(self.oTempDir.name, 'stacv_junit.xml')
        self.sSuiteName = sSuiteName

    def tearDown(self):
        self.oTempDir.cleanup()

    def run_check(self):
        oArgs = argparse.Namespace(interface_file=self.sInterfaceFile, report=None, junit=self.sJunitFile)
        oDateTime = datetime.datetime(2026, 10, 24, 20, 0, 0)
        lArgv = ['stacv', 'check', self.sInterfaceFile, '--junit', self.sJunitFile]
        with contextlib.redirect_stdout(io.StringIO()):
            return check.execute(oArgs, oDateTime, lArgv)

    def find_testcase(self, sRuleId):
        oRoot = xml.etree.ElementTree.parse(self.sJunitFile).getroot()
        for oSuite in oRoot.findall('testsuite'):
            if oSuite.get('name') == self.sSuiteName:
                for oTestcase in oSuite.findall('testcase'):
                    if oTestcase.get('name') == sRuleId:
                        return oTestcase
        raise ValueError(f'{self.sSuiteName} {sRuleId} is not in the JUnit file')

    def assert_rule_passed(self, sRuleId):
        oTestcase = self.find_testcase(sRuleId)
        self.assertEqual([], list(oTestcase))

    def assert_rule_failed(self, sRuleId):
        oTestcase = self.find_testcase(sRuleId)
        self.assertIsNotNone(oTestcase.find('failure'))
