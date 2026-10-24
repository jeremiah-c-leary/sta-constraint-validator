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

# Every setup timing report in this file has a requirement of 10.000ns, on lines 82 and 226.
# Every hold timing report has a requirement of 0.000ns, on lines 21 and 165.
sTimingReport = os.path.abspath(os.path.join(sParseDir, 'O_DAC_DATA_timing.rpt'))
lSetupRequirementLines = [82, 226]
lHoldRequirementLines = [21, 165]

sSuiteName = 'O_DAC_DATA.SDR-SS-O'
sRuleId = 's4_requirement_001'

# With a launch clock period of 10.000ns and a capture clock period of 50.000ns:
#    launch edge 8   is at (10.000 / 2) * 8 = 40.000ns
#    capture edge C  is at (50.000 / 2) * 2 = 50.000ns
# which gives a setup requirement of 50.000 - 40.000 = 10.000ns.
iPassingLaunchSetupEdge = 8
sPassingCaptureSetupEdge = 'C'
fPassingCapturePeriod = 50.0


def build_config_text(sPartFile, sTracesFile, sTimingReportFile, oSetupEdges):
    lText = []
    lText.append('description = "s4_requirement_001 test"')
    lText.append('interface = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append(f'launch_clock = {{name = "clk_100mhz", period = 10.000, setup_edge = {oSetupEdges.launch_edge}, hold_edge = 0}}')
    lText.append(f'capture_clock = {{port = "O_DAC_SCLK", name = "dac_sclk", period = {oSetupEdges.capture_period}, setup_edge = "{oSetupEdges.capture_edge}", hold_edge = "A"}}')
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
    lText.append('capture_edge = "Rising"')
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


class SetupEdges():

    def __init__(self, iLaunchEdge, sCaptureEdge, fCapturePeriod):
        self.launch_edge = iLaunchEdge
        self.capture_edge = sCaptureEdge
        self.capture_period = fCapturePeriod


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

    def execute_with_setup_edges(self, iLaunchEdge, sCaptureEdge):
        oSetupEdges = SetupEdges(iLaunchEdge, sCaptureEdge, fPassingCapturePeriod)
        return self.execute(oSetupEdges, sTimingReport)

    def execute_with_capture_period(self, fCapturePeriod):
        oSetupEdges = SetupEdges(iPassingLaunchSetupEdge, sPassingCaptureSetupEdge, fCapturePeriod)
        return self.execute(oSetupEdges, sTimingReport)

    def execute_with_requirement_lines_changed(self, lLineNumbers, sOld, sNew):
        lLines = read_lines(sTimingReport)
        for iLineNumber in lLineNumbers:
            self.assertIn(sOld, lLines[iLineNumber - 1])
            lLines[iLineNumber - 1] = lLines[iLineNumber - 1].replace(sOld, sNew)
        write_file(self.sChangedTimingReport, '\n'.join(lLines))
        oSetupEdges = SetupEdges(iPassingLaunchSetupEdge, sPassingCaptureSetupEdge, fPassingCapturePeriod)
        return self.execute(oSetupEdges, self.sChangedTimingReport)

    def execute(self, oSetupEdges, sTimingReportFile):
        write_file(self.sConfigFile, build_config_text(self.sPartFile, self.sTracesFile, sTimingReportFile, oSetupEdges))
        write_file(self.sPartFile, build_part_text())
        write_file(self.sTracesFile, build_traces_text())
        oArgs = argparse.Namespace(config_file=self.sConfigFile, report=None, junit=self.sJunitFile)
        oDateTime = datetime.datetime(2026, 10, 24, 20, 0, 0)
        lArgv = ['stacv', 'check', self.sConfigFile, '--junit', self.sJunitFile]
        with contextlib.redirect_stdout(io.StringIO()):
            return check.execute(oArgs, oDateTime, lArgv)

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

    def test_passes_when_setup_requirement_matches_configured_setup_edges(self):
        self.execute_with_setup_edges(iPassingLaunchSetupEdge, sPassingCaptureSetupEdge)

        self.assert_rule_passed()

    def test_exit_code_is_zero_when_setup_requirement_matches(self):
        iExitCode = self.execute_with_setup_edges(iPassingLaunchSetupEdge, sPassingCaptureSetupEdge)

        self.assertEqual(0, iExitCode)

    def test_fails_when_launch_setup_edge_differs(self):
        # (50.000 / 2) * 2 - (10.000 / 2) * 6 = 50.000 - 30.000 = 20.000
        self.execute_with_setup_edges(6, sPassingCaptureSetupEdge)

        self.assert_rule_failed()

    def test_exit_code_is_one_when_setup_requirement_differs(self):
        iExitCode = self.execute_with_setup_edges(6, sPassingCaptureSetupEdge)

        self.assertEqual(1, iExitCode)

    def test_fails_when_capture_setup_edge_differs(self):
        # (50.000 / 2) * 3 - (10.000 / 2) * 8 = 75.000 - 40.000 = 35.000
        self.execute_with_setup_edges(iPassingLaunchSetupEdge, 'D')

        self.assert_rule_failed()

    def test_passes_when_a_later_pair_of_edges_has_the_same_setup_requirement(self):
        # (50.000 / 2) * 4 - (10.000 / 2) * 18 = 100.000 - 90.000 = 10.000
        self.execute_with_setup_edges(18, 'E')

        self.assert_rule_passed()

    def test_passes_when_configured_setup_requirement_is_above_by_less_than_rounding(self):
        # (50.0004 / 2) * 2 - 40.000 = 10.0004
        self.execute_with_capture_period(50.0004)

        self.assert_rule_passed()

    def test_passes_when_configured_setup_requirement_is_below_by_less_than_rounding(self):
        # (49.9996 / 2) * 2 - 40.000 = 9.9996
        self.execute_with_capture_period(49.9996)

        self.assert_rule_passed()

    def test_fails_when_configured_setup_requirement_is_above_by_more_than_rounding(self):
        # (50.0006 / 2) * 2 - 40.000 = 10.0006
        self.execute_with_capture_period(50.0006)

        self.assert_rule_failed()

    def test_fails_when_configured_setup_requirement_is_below_by_more_than_rounding(self):
        # (49.9994 / 2) * 2 - 40.000 = 9.9994
        self.execute_with_capture_period(49.9994)

        self.assert_rule_failed()

    def test_fails_when_one_setup_timing_report_has_a_different_requirement(self):
        self.execute_with_requirement_lines_changed([226], 'Requirement:            10.000ns', 'Requirement:            20.000ns')

        self.assert_rule_failed()

    def test_ignores_requirement_of_hold_timing_reports(self):
        self.execute_with_requirement_lines_changed(lHoldRequirementLines, 'Requirement:            0.000ns', 'Requirement:            5.000ns')

        self.assert_rule_passed()

    def test_failure_lists_each_setup_timing_report_with_a_different_requirement(self):
        self.execute_with_setup_edges(iPassingLaunchSetupEdge, 'D')

        lExpected = []
        for iLineNumber in lSetupRequirementLines:
            lExpected.append(f'{sTimingReport}:{iLineNumber}  setup requirement 10.000ns, configured setup requirement 35.000ns')
        oFailure = self.find_rule_testcase().find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)

    def test_failure_lists_only_the_setup_timing_report_with_a_different_requirement(self):
        self.execute_with_requirement_lines_changed([226], 'Requirement:            10.000ns', 'Requirement:            20.000ns')

        lExpected = []
        lExpected.append(f'{self.sChangedTimingReport}:226  setup requirement 20.000ns, configured setup requirement 10.000ns')
        oFailure = self.find_rule_testcase().find('failure')
        self.assertEqual('\n'.join(lExpected), oFailure.text)
