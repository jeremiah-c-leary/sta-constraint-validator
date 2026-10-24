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
sRuleId = 's0_trace_001'

# The part has one pin, SDIN, clocked by SCLK.
# The port O_DAC_DATA is captured by the clock on port O_DAC_SCLK.
# These delays, with a part setup and hold of 0.5, pass every stage 3 rule.
fDataDelay = 2.0
fClockDelay = 0.5


def create_trace(sName, sDevicePin, sPartPin, sDirection, fDelay):
    dTrace = {}
    dTrace['name'] = sName
    dTrace['device_pin'] = sDevicePin
    dTrace['part_pin'] = sPartPin
    dTrace['direction'] = sDirection
    dTrace['delay'] = fDelay
    return dTrace


def create_data_trace(sDevicePin, sPartPin):
    return create_trace('data_output', sDevicePin, sPartPin, 'device_to_part', fDataDelay)


def create_clock_trace(sDevicePin, sPartPin):
    return create_trace('clock', sDevicePin, sPartPin, 'device_to_part', fClockDelay)


def create_passing_data_trace():
    return create_data_trace('O_DAC_DATA', 'SDIN')


def create_passing_clock_trace():
    return create_clock_trace('O_DAC_SCLK', 'SCLK')


def create_passing_traces():
    lTraces = []
    lTraces.append(create_passing_data_trace())
    lTraces.append(create_passing_clock_trace())
    return lTraces


def build_config_text(sPartFile, sTracesFile):
    lText = []
    lText.append('description = "s0_trace_001 test"')
    lText.append('interface = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append('launch_clock = {name = "clk_100mhz", period = 10}')
    lText.append('capture_clock = {port = "O_DAC_SCLK", name = "dac_sclk", period = 50}')
    lText.append(f'timing_reports = ["{sTimingReport}"]')
    return '\n'.join(lText)


def build_part_text():
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


def build_traces_text(lTraces):
    lText = []
    for dTrace in lTraces:
        lText.append('[[trace]]')
        lText.append(f'name = "{dTrace["name"]}"')
        lText.append(f'device_pin = "{dTrace["device_pin"]}"')
        lText.append(f'part_pin = "{dTrace["part_pin"]}"')
        lText.append(f'{dTrace["direction"]} = {{max_delay = {dTrace["delay"]}, min_delay = {dTrace["delay"]}}}')
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

    def execute(self, lTraces):
        write_file(self.sConfigFile, build_config_text(self.sPartFile, self.sTracesFile))
        write_file(self.sPartFile, build_part_text())
        write_file(self.sTracesFile, build_traces_text(lTraces))
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

    def assert_rule_passed(self):
        oTestcase = self.find_testcase(sRuleId)
        self.assertEqual([], list(oTestcase))

    def assert_rule_failed(self):
        oTestcase = self.find_testcase(sRuleId)
        self.assertIsNotNone(oTestcase.find('failure'))

    def test_passes_when_data_trace_and_clock_trace_exist(self):
        self.execute(create_passing_traces())

        self.assert_rule_passed()

    def test_fails_when_no_trace_has_port_as_device_pin(self):
        lTraces = []
        lTraces.append(create_data_trace('O_OTHER_DATA', 'SDIN'))
        lTraces.append(create_passing_clock_trace())
        self.execute(lTraces)

        self.assert_rule_failed()

    def test_fails_when_data_trace_part_pin_is_not_a_pin_of_the_part(self):
        lTraces = []
        lTraces.append(create_data_trace('O_DAC_DATA', 'SDO'))
        lTraces.append(create_passing_clock_trace())
        self.execute(lTraces)

        self.assert_rule_failed()

    def test_fails_when_no_trace_has_capture_clock_port_as_device_pin(self):
        lTraces = []
        lTraces.append(create_passing_data_trace())
        lTraces.append(create_clock_trace('O_OTHER_SCLK', 'SCLK'))
        self.execute(lTraces)

        self.assert_rule_failed()

    def test_fails_when_capture_clock_trace_part_pin_is_not_the_clock_pin(self):
        lTraces = []
        lTraces.append(create_passing_data_trace())
        lTraces.append(create_clock_trace('O_DAC_SCLK', 'CSF'))
        self.execute(lTraces)

        self.assert_rule_failed()

    def test_fails_when_clock_device_pin_and_part_pin_match_on_different_traces(self):
        # Neither trace connects O_DAC_SCLK to SCLK
        lTraces = []
        lTraces.append(create_passing_data_trace())
        lTraces.append(create_clock_trace('O_DAC_SCLK', 'CSF'))
        lTraces.append(create_clock_trace('O_OTHER_SCLK', 'SCLK'))
        self.execute(lTraces)

        self.assert_rule_failed()

    def test_passes_when_another_clock_trace_to_the_clock_pin_is_listed_first(self):
        lTraces = []
        lTraces.append(create_passing_data_trace())
        lTraces.append(create_trace('other_clock', 'O_OTHER_SCLK', 'SCLK', 'device_to_part', 9.0))
        lTraces.append(create_passing_clock_trace())
        self.execute(lTraces)

        self.assert_rule_passed()

    def test_stage_3_uses_clock_trace_from_capture_clock_port_when_another_is_listed_first(self):
        # With the 9.0 delay of O_OTHER_SCLK the maximum output delay would be 0.5 + 2.0 - 9.0 = -6.500
        lTraces = []
        lTraces.append(create_passing_data_trace())
        lTraces.append(create_trace('other_clock', 'O_OTHER_SCLK', 'SCLK', 'device_to_part', 9.0))
        lTraces.append(create_passing_clock_trace())
        self.execute(lTraces)

        self.assertEqual([], list(self.find_testcase('s3_output_delay_001')))

    def test_fails_when_data_trace_has_no_device_to_part_delays(self):
        lTraces = []
        lTraces.append(create_trace('data_output', 'O_DAC_DATA', 'SDIN', 'part_to_device', fDataDelay))
        lTraces.append(create_passing_clock_trace())
        self.execute(lTraces)

        self.assert_rule_failed()

    def test_fails_when_clock_trace_has_no_device_to_part_delays(self):
        lTraces = []
        lTraces.append(create_passing_data_trace())
        lTraces.append(create_trace('clock', 'O_DAC_SCLK', 'SCLK', 'part_to_device', fClockDelay))
        self.execute(lTraces)

        self.assert_rule_failed()

    def test_passes_when_unrelated_traces_exist(self):
        lTraces = []
        lTraces.append(create_data_trace('O_OTHER_DATA', 'SDO'))
        lTraces.append(create_clock_trace('O_DAC_CSF', 'CSF'))
        lTraces.extend(create_passing_traces())
        self.execute(lTraces)

        self.assert_rule_passed()

    def test_skips_stage_3_when_data_trace_is_missing(self):
        lTraces = []
        lTraces.append(create_passing_clock_trace())
        self.execute(lTraces)

        oSkipped = self.find_testcase('s3_output_delay_001').find('skipped')
        self.assertEqual('stage 0 failed', oSkipped.get('message'))

    def test_exit_code_is_one_when_data_trace_is_missing(self):
        lTraces = []
        lTraces.append(create_passing_clock_trace())
        iExitCode = self.execute(lTraces)

        self.assertEqual(1, iExitCode)
