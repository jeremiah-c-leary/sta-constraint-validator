import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__

TRACE_KEYS = 'name, device_pin, part_pin, device_to_part, part_to_device, source, source_to_device, source_to_part'


def build_interface_text():
    lText = []
    lText.append('description = "traces errors test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append('part = "part.toml"')
    lText.append('part_interface = "INTERFACE_NAME"')
    lText.append('traces = "traces.toml"')
    lText.append('[[clock]]')
    lText.append('name = "clk_capture"')
    lText.append('period = 40.0')
    lText.append('port = "O_CLK"')
    lText.append('[[port]]')
    lText.append('status = "defer"')
    lText.append('name = "O_DATA"')
    return '\n'.join(lText) + '\n'


PART_TEXT = """[properties]
manufacturer = "MANUFACTURER"
part_number = "PART_NUMBER"

[datasheet]
name = "DATASHEET_NAME"
url = "DATASHEET_URL"
version = "DATASHEET_VERSION"

[[interface]]
name = "INTERFACE_NAME"

[[interface.pin]]
name = "DATA_IN"
methodology = "SDR-SS-I"
clock = {pin = "CLK", max_frequency = 25}
capture_edge = "Falling"
setup = {value = 10, symbol = "tSetup", source = "Table X"}
hold = {value = 10, symbol = "tHold", source = "Table X"}
"""


def build_trace(sName='clock', sDevicePin='device_pin = "O_CLK"', sPartPin='part_pin = "CLK"', sDelays='device_to_part = {max_delay = 3.0, min_delay = 1.0}'):
    lText = ['[[trace]]']
    if sName is not None:
        lText.append(f'name = "{sName}"')
    for sLine in [sDevicePin, sPartPin, sDelays]:
        if sLine is not None:
            lText.append(sLine)
    return '\n'.join(lText)


class TracesTestCase(unittest.TestCase):
    '''
    The traces file is read through stacv visualize block_diagram, which reads it before the part file.
    '''

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        self.sTracesFile = os.path.join(self.sDirectory, 'traces.toml')
        self.write_file('interface.toml', build_interface_text())
        self.write_file('part.toml', PART_TEXT)

    def write_file(self, sFilename, sText):
        with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
            oFile.write(sText)

    def run_block_diagram(self, lTracesText):
        self.write_file('traces.toml', '\n'.join(lTracesText) + '\n')
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        lArgv = ['stacv', 'visualize', 'block_diagram', os.path.join(self.sDirectory, 'interface.toml')]
        with mock.patch('sys.argv', lArgv):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def assert_error(self, lTracesText, sIdentifier, sMessage):
        iExitCode = self.run_block_diagram(lTracesText)
        self.assertEqual(f'ERROR: [{sIdentifier}] {self.sTracesFile} {sMessage}\n', self.oStderr.getvalue())
        self.assertEqual('', self.oStdout.getvalue())
        self.assertEqual(2, iExitCode)


class TestTracesErrors(TracesTestCase):

    def test_invalid_toml_is_an_error(self):
        iExitCode = self.run_block_diagram(['[[trace]', 'name = "clock"'])
        self.assertTrue(self.oStderr.getvalue().startswith(f'ERROR: [traces_config_001] {self.sTracesFile} is not valid TOML: '))
        self.assertEqual(2, iExitCode)

    def test_traces_file_without_a_trace_table_is_an_error(self):
        self.assert_error(['default_delay = {max_delay = 1.0, min_delay = 0.0}'], 'traces_config_002', 'missing required key "trace"')

    def test_trace_without_a_name_is_named_by_its_number(self):
        self.assert_error([build_trace(), build_trace(sName=None)], 'traces_config_002', 'missing required key "name" in trace number 2')

    def test_trace_without_a_part_pin_is_an_error(self):
        self.assert_error([build_trace(sPartPin=None)], 'traces_config_002', 'missing required key "part_pin" in trace clock')

    def test_default_delay_without_a_minimum_delay_is_an_error(self):
        self.assert_error(['default_delay = {max_delay = 1.0}', build_trace()], 'traces_config_002', 'missing required key "min_delay" in default_delay')

    def test_trace_name_must_be_a_string(self):
        self.assert_error(['[[trace]]', 'name = 5', 'device_pin = "O_CLK"', 'part_pin = "CLK"'], 'traces_config_003', 'key "name" in trace number 1 must be a non-empty string')

    def test_trace_direction_must_be_a_table(self):
        self.assert_error([build_trace(sDelays='device_to_part = 3.0')], 'traces_config_003', 'key "device_to_part" in trace clock must be a table')

    def test_delay_must_be_a_number(self):
        self.assert_error([build_trace(sDelays='device_to_part = {max_delay = "3.0", min_delay = 1.0}')], 'traces_config_003', 'key "max_delay" in device_to_part of trace clock must be a number')

    def test_unknown_top_level_key_is_an_error(self):
        self.assert_error(['default_dealy = {max_delay = 1.0, min_delay = 0.0}', build_trace()], 'traces_config_004', 'key "default_dealy" is not a key stacv reads; the keys are default_delay, trace')

    def test_misspelled_trace_key_is_unknown_rather_than_missing(self):
        self.assert_error([build_trace(sDevicePin='devcie_pin = "O_CLK"')], 'traces_config_004', f'key "devcie_pin" in trace clock is not a key stacv reads; the keys are {TRACE_KEYS}')

    def test_unknown_delay_key_is_an_error(self):
        self.assert_error([build_trace(sDelays='device_to_part = {max_dealy = 3.0, min_delay = 1.0}')], 'traces_config_004', 'key "max_dealy" in device_to_part of trace clock is not a key stacv reads; the keys are max_delay, min_delay')

    def test_valid_traces_file_draws_the_block_diagram(self):
        iExitCode = self.run_block_diagram([build_trace()])
        self.assertEqual('', self.oStderr.getvalue())
        self.assertEqual(0, iExitCode)
