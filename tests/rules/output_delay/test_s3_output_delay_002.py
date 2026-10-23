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

# Setup reports at both process corners have an output delay of 2.000ns.
# Hold reports at both process corners have an output delay of 1.000ns.
sTimingReport = os.path.abspath(os.path.join(sParseDir, 'O_DAC_DATA_timing.rpt'))

sSuiteName = 'O_DAC_DATA.SDR-SS-O'
sRuleId = 's3_output_delay_002'

# With these traces, a part hold of 0.5 gives a calculated minimum output delay of:
#   -0.5 + 2.0 - 0.5 = 1.000
# and a part setup of 0.5 gives a calculated maximum output delay of:
#    0.5 + 2.0 - 0.5 = 2.000
fPassingSetup = 0.5
fPassingHold = 0.5


def create_trace(sName, sDevicePin, sPartPin, fMaxDelay, fMinDelay):
    dTrace = {}
    dTrace['name'] = sName
    dTrace['device_pin'] = sDevicePin
    dTrace['part_pin'] = sPartPin
    dTrace['max_delay'] = fMaxDelay
    dTrace['min_delay'] = fMinDelay
    return dTrace


def create_data_trace(fMaxDelay, fMinDelay):
    return create_trace('data_output', 'O_DAC_DATA', 'SDIN', fMaxDelay, fMinDelay)


def create_clock_trace(fMaxDelay, fMinDelay):
    return create_trace('clock', 'O_DAC_SCLK', 'SCLK', fMaxDelay, fMinDelay)


def create_passing_traces():
    lTraces = []
    lTraces.append(create_data_trace(2.0, 2.0))
    lTraces.append(create_clock_trace(0.5, 0.5))
    return lTraces


def build_config_text(sPartFile, sTracesFile):
    lText = []
    lText.append('description = "s3_output_delay_002 test"')
    lText.append('interface = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append('launch_clock = {name = "clk_100mhz", period = 10.000}')
    lText.append('capture_clock = {port = "O_DAC_SCLK", name = "dac_sclk", period = 50}')
    lText.append(f'timing_reports = ["{sTimingReport}"]')
    return '\n'.join(lText)


def build_part_text(fSetup, fHold):
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
    lText.append(f'setup = {{value = {fSetup}, symbol = "tSDIS", source = "Table 7.6"}}')
    lText.append(f'hold = {{value = {fHold}, symbol = "tSDIH", source = "Table 7.6"}}')
    return '\n'.join(lText)


def build_traces_text(lTraces):
    lText = []
    for dTrace in lTraces:
        lText.append('[[trace]]')
        lText.append(f'name = "{dTrace["name"]}"')
        lText.append(f'device_pin = "{dTrace["device_pin"]}"')
        lText.append(f'part_pin = "{dTrace["part_pin"]}"')
        lText.append(f'device_to_part = {{max_delay = {dTrace["max_delay"]}, min_delay = {dTrace["min_delay"]}}}')
    return '\n'.join(lText)


def write_file(sFilename, sText):
    with open(sFilename, 'w') as oFile:
        oFile.write(sText)


class Test(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sConfigFile = os.path.join(self.oTempDir.name, 'stacv.toml')
        self.sPartFile = os.path.join(self.oTempDir.name, 'part.toml')
        self.sTracesFile = os.path.join(self.oTempDir.name, 'traces.toml')
        self.sJunitFile = os.path.join(self.oTempDir.name, 'stacv_junit.xml')

    def tearDown(self):
        self.oTempDir.cleanup()

    def execute(self, fSetup, fHold, lTraces):
        write_file(self.sConfigFile, build_config_text(self.sPartFile, self.sTracesFile))
        write_file(self.sPartFile, build_part_text(fSetup, fHold))
        write_file(self.sTracesFile, build_traces_text(lTraces))
        oArgs = argparse.Namespace(config_file=self.sConfigFile, report=None, junit=self.sJunitFile)
        oDateTime = datetime.datetime(2026, 10, 22, 20, 0, 0)
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

    def test_passes_when_output_delay_matches_calculated_output_delay(self):
        self.execute(fPassingSetup, fPassingHold, create_passing_traces())

        self.assert_rule_passed()

    def test_exit_code_is_zero_when_output_delay_matches_calculated_output_delay(self):
        iExitCode = self.execute(fPassingSetup, fPassingHold, create_passing_traces())

        self.assertEqual(0, iExitCode)

    def test_fails_when_part_hold_moves_calculated_output_delay(self):
        # -10.0 + 2.0 - 0.5 = -8.500
        self.execute(fPassingSetup, 10.0, create_passing_traces())

        self.assert_rule_failed()

    def test_exit_code_is_one_when_output_delay_does_not_match(self):
        iExitCode = self.execute(fPassingSetup, 10.0, create_passing_traces())

        self.assertEqual(1, iExitCode)

    def test_passes_when_calculated_output_delay_is_above_by_less_than_rounding(self):
        # -0.4996 + 2.0 - 0.5 = 1.0004
        self.execute(fPassingSetup, 0.4996, create_passing_traces())

        self.assert_rule_passed()

    def test_passes_when_calculated_output_delay_is_below_by_less_than_rounding(self):
        # -0.5004 + 2.0 - 0.5 = 0.9996
        self.execute(fPassingSetup, 0.5004, create_passing_traces())

        self.assert_rule_passed()

    def test_fails_when_calculated_output_delay_is_above_by_more_than_rounding(self):
        # -0.4994 + 2.0 - 0.5 = 1.0006
        self.execute(fPassingSetup, 0.4994, create_passing_traces())

        self.assert_rule_failed()

    def test_fails_when_calculated_output_delay_is_below_by_more_than_rounding(self):
        # -0.5006 + 2.0 - 0.5 = 0.9994
        self.execute(fPassingSetup, 0.5006, create_passing_traces())

        self.assert_rule_failed()

    def test_uses_minimum_delay_of_data_trace(self):
        # -0.5 + 1.5 - 0.5 = 0.500
        lTraces = []
        lTraces.append(create_data_trace(2.0, 1.5))
        lTraces.append(create_clock_trace(0.5, 0.5))
        self.execute(fPassingSetup, fPassingHold, lTraces)

        self.assert_rule_failed()

    def test_uses_maximum_delay_of_clock_trace(self):
        # -0.5 + 2.0 - 1.0 = 0.500
        lTraces = []
        lTraces.append(create_data_trace(2.0, 2.0))
        lTraces.append(create_clock_trace(1.0, 0.5))
        self.execute(fPassingSetup, fPassingHold, lTraces)

        self.assert_rule_failed()

    def test_ignores_part_setup_and_setup_trace_delays(self):
        # Hold:  -0.5 + 2.0 - 0.5 = 1.000, which matches
        # Setup:  9.0 + 9.0 - 0.0 = 18.000, which is checked by s3_output_delay_001
        lTraces = []
        lTraces.append(create_data_trace(9.0, 2.0))
        lTraces.append(create_clock_trace(0.5, 0.0))
        self.execute(9.0, fPassingHold, lTraces)

        self.assert_rule_passed()

    def test_finds_data_trace_by_device_pin(self):
        lTraces = []
        lTraces.append(create_trace('other_output', 'O_OTHER_DATA', 'SDO', 9.0, 9.0))
        lTraces.extend(create_passing_traces())
        self.execute(fPassingSetup, fPassingHold, lTraces)

        self.assert_rule_passed()

    def test_finds_clock_trace_by_clock_pin_of_part_pin(self):
        lTraces = []
        lTraces.append(create_data_trace(2.0, 2.0))
        lTraces.append(create_trace('chip_select', 'O_DAC_CSF', 'CSF', 9.0, 9.0))
        lTraces.append(create_clock_trace(0.5, 0.5))
        self.execute(fPassingSetup, fPassingHold, lTraces)

        self.assert_rule_passed()
