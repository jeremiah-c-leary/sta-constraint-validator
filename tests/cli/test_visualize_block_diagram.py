import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__


def build_interface_text(sMissingTimingReport, sClockPort):
    lText = []
    lText.append('description = "block diagram test"')
    lText.append('interface = "DAC_SPI_1"')
    lText.append('part = "part.toml"')
    lText.append('traces = "traces.toml"')
    lText.append('')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append('launch_clock = {name = "clk_launch", period = 10, setup_edge = 4, hold_edge = 4}')
    lText.append(f'capture_clock = {{port = "{sClockPort}", name = "clk_capture", period = 40, setup_edge = "C", hold_edge = "A"}}')
    lText.append(f'timing_reports = ["{sMissingTimingReport}"]')
    return '\n'.join(lText) + '\n'


def build_part_text(sPartNumber):
    lText = []
    lText.append('[properties]')
    lText.append('manufacturer = "Texas Instruments"')
    lText.append(f'part_number = "{sPartNumber}"')
    lText.append('')
    lText.append('[datasheet]')
    lText.append('name = "datasheet"')
    lText.append('url = "https://www.ti.com"')
    lText.append('version = "A"')
    lText.append('')
    lText.append('[[interface]]')
    lText.append('name = "Serial Interface"')
    lText.append('')
    lText.append('[[interface.pin]]')
    lText.append('name = "SDIN"')
    lText.append('methodology = "SDR-SS-I"')
    lText.append('clock = {pin = "SCLK", max_frequency = 25}')
    lText.append('capture_edge = "Falling"')
    lText.append('setup = {value = 10, symbol = "tSDIS", source = "Table 7.6"}')
    lText.append('hold = {value = 10, symbol = "tSDIH", source = "Table 7.6"}')
    return '\n'.join(lText) + '\n'


def output_trace(sName, sDevicePin, sPartPin):
    return build_trace_text(sName, sDevicePin, sPartPin, 'device_to_part')


def input_trace(sName, sDevicePin, sPartPin):
    return build_trace_text(sName, sDevicePin, sPartPin, 'part_to_device')


def build_trace_text(sName, sDevicePin, sPartPin, sDirection):
    lText = []
    lText.append('[[trace]]')
    lText.append(f'name = "{sName}"')
    lText.append(f'device_pin = "{sDevicePin}"')
    lText.append(f'part_pin = "{sPartPin}"')
    lText.append(f'{sDirection} = {{max_delay = 3.00, min_delay = 1.00}}')
    return '\n'.join(lText)


def build_dac81404_traces():
    lTraces = []
    lTraces.append(output_trace('data_output', 'O_DAC_DATA', 'SDIN'))
    lTraces.append(output_trace('chip_select', 'O_DAC_CSF', 'CSF'))
    lTraces.append(input_trace('data_input', 'I_DAC_DATA', 'SDO'))
    lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
    return lTraces


class BlockDiagramTestCase(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        self.sInterfaceFile = os.path.join(self.sDirectory, 'interface.toml')
        self.sMissingTimingReport = os.path.join(self.sDirectory, 'not_written_yet.rpt')

    def write_file(self, sFilename, sText):
        with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
            oFile.write(sText)

    def run_visualize_block_diagram(self, lTraces, sPartNumber='DAC81404', sClockPort='O_DAC_SCLK'):
        self.write_file('interface.toml', build_interface_text(self.sMissingTimingReport, sClockPort))
        self.write_file('part.toml', build_part_text(sPartNumber))
        self.write_file('traces.toml', '\n\n'.join(lTraces) + '\n')
        lArgv = ['stacv', 'visualize', 'block_diagram', self.sInterfaceFile]
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', lArgv):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def assert_rows_drawn(self, lExpectedRows):
        self.assertIn('\n'.join(lExpectedRows) + '\n', self.oStdout.getvalue())


class TestVisualizeBlockDiagramDispatch(BlockDiagramTestCase):

    def test_exits_with_zero(self):
        self.assertEqual(0, self.run_visualize_block_diagram(build_dac81404_traces()))

    def test_writes_nothing_to_stderr(self):
        self.run_visualize_block_diagram(build_dac81404_traces())
        self.assertEqual('', self.oStderr.getvalue())


class TestVisualizeBlockDiagramExample(BlockDiagramTestCase):

    def test_draws_the_example_block_diagram(self):
        self.run_visualize_block_diagram(build_dac81404_traces())
        lExpected = []
        lExpected.append('--------------+                       +------------')
        lExpected.append('  Device      |                       |  DAC81404')
        lExpected.append('              |                       |')
        lExpected.append('  O_DAC_DATA [X] --- data_output --> [X] SDIN')
        lExpected.append('              |                       |')
        lExpected.append('  O_DAC_CSF  [X] --- chip_select --> [X] CSF')
        lExpected.append('              |                       |')
        lExpected.append('  I_DAC_DATA [X] <-- data_input ---- [X] SDO')
        lExpected.append('              |                       |')
        lExpected.append('  O_DAC_SCLK [X] --- clock --------> [X] SCLK')
        lExpected.append('              |                       |')
        lExpected.append('--------------+                       +------------')
        self.assert_rows_drawn(lExpected)
