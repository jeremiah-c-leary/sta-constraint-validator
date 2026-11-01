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


# The SDR-SS-RT rule tests check the example's I_DAC_DATA timing report, which has the same four reports, each 77 lines long.
sRoundTripTimingReport = os.path.join(sExampleDir, 'timing_reports', 'I_DAC_DATA_timing.rpt')
sRoundTripSuiteName = 'I_DAC_DATA.SDR-SS-RT'

# Lines of the first report, the setup report at the Slow Process Corner.
iRoundTripRequirementLine = 21
iInputDelayLine = 24
iLaunchClockPathEndLine = 48
iDataPathStartLine = 52

# With the passing round trip part and traces, the calculated input delays match the timing report:
#    maximum:  clock max_delay + cko_max + data max_delay = 3.0 + 30 + 1.0 = 34.000
#    minimum:  clock min_delay + cko_min + data min_delay = 1.0 +  0 + 0.0 =  1.000
sPassingLaunchEdge = 'Rising'
fPassingClockToOutMax = 30.0
fPassingClockToOutMin = 0.0
fPassingDataInputMaxDelay = 1.0
fPassingDataInputMinDelay = 0.0


def build_round_trip_config_text(sPartFile, sTracesFile, sTimingReportFile, sPortName='I_DAC_DATA', sClockPort='O_DAC_SCLK'):
    lText = []
    lText.append('description = "SDR-SS-RT rule test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[clock]]')
    lText.append('name = "clk_100mhz"')
    lText.append('period = 10.000')
    lText.append('[[clock]]')
    lText.append('name = "dac_sclk_rd"')
    lText.append('period = 80.000')
    lText.append(f'port = "{sClockPort}"')
    lText.append('[[port]]')
    lText.append(f'name = "{sPortName}"')
    lText.append('methodology = "SDR-SS-RT"')
    lText.append('launch_clock = {name = "dac_sclk_rd", setup_edge = 2, hold_edge = 2}')
    lText.append('capture_clock = {name = "clk_100mhz", setup_edge = "Y", hold_edge = "I"}')
    lText.append(f'timing_reports = ["{sTimingReportFile}"]')
    return '\n'.join(lText)


def build_round_trip_part_text(sLaunchEdge=sPassingLaunchEdge, fClockToOutMax=fPassingClockToOutMax, fClockToOutMin=fPassingClockToOutMin):
    lText = []
    lText.append(build_passing_part_text())
    lText.append('[[interface.pin]]')
    lText.append('name = "SDO"')
    lText.append('methodology = "SDR-SS-RT"')
    lText.append('clock = {pin = "SCLK", max_frequency = 12.5}')
    lText.append(f'cko_max = {{value = {fClockToOutMax}, symbol = "tSDODLY", source = "Table 7.8"}}')
    lText.append(f'cko_min = {{value = {fClockToOutMin}, symbol = "tSDODLY", source = "Table 7.8"}}')
    lText.append(f'launch_edge = "{sLaunchEdge}"')
    return '\n'.join(lText)


def build_round_trip_traces_text(fDataMaxDelay=fPassingDataInputMaxDelay, fDataMinDelay=fPassingDataInputMinDelay, bWithDataInput=True):
    lText = []
    if bWithDataInput:
        lText.append('[[trace]]')
        lText.append('name = "data_input"')
        lText.append('device_pin = "I_DAC_DATA"')
        lText.append('part_pin = "SDO"')
        lText.append(f'part_to_device = {{max_delay = {fDataMaxDelay}, min_delay = {fDataMinDelay}}}')
    lText.append('[[trace]]')
    lText.append('name = "clock"')
    lText.append('device_pin = "O_DAC_SCLK"')
    lText.append('part_pin = "SCLK"')
    lText.append(f'device_to_part = {{max_delay = {fPassingMaxDelay}, min_delay = {fPassingMinDelay}}}')
    return '\n'.join(lText)


class RoundTripRuleTestCase(RuleTestCase):
    '''
    Runs check on an SDR-SS-RT port, with the passing inputs unless a test changes one.
    '''

    def setUp(self):
        RuleTestCase.setUp(self)
        self.sSuiteName = sRoundTripSuiteName
        self.sChangedTimingReport = os.path.join(self.oTempDir.name, 'I_DAC_DATA_timing.rpt')

    def execute_round_trip(self, sTimingReportFile=sRoundTripTimingReport, sPortName='I_DAC_DATA', sClockPort='O_DAC_SCLK', sPartText=None, sTracesText=None):
        self.sSuiteName = f'{sPortName}.SDR-SS-RT'
        if sPartText is None:
            sPartText = build_round_trip_part_text()
        if sTracesText is None:
            sTracesText = build_round_trip_traces_text()
        write_file(self.sInterfaceFile, build_round_trip_config_text(self.sPartFile, self.sTracesFile, sTimingReportFile, sPortName, sClockPort))
        write_file(self.sPartFile, sPartText)
        write_file(self.sTracesFile, sTracesText)
        return self.run_check()

    def execute_round_trip_with_lines_changed(self, lLineNumbers, sOld, sNew):
        lLines = read_lines(sRoundTripTimingReport)
        for iLineNumber in lLineNumbers:
            self.assertIn(sOld, lLines[iLineNumber - 1])
            lLines[iLineNumber - 1] = lLines[iLineNumber - 1].replace(sOld, sNew)
        write_file(self.sChangedTimingReport, '\n'.join(lLines))
        return self.execute_round_trip(self.sChangedTimingReport)
