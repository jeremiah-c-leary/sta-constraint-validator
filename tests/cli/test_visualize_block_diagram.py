import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__


def build_interface_text(lPortNames, sMissingTimingReport, sClockPort):
    lText = []
    lText.append('description = "block diagram test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append('part = "part.toml"')
    lText.append('part_interface = "Serial Interface"')
    lText.append('traces = "traces.toml"')
    lText.append('[[clock]]')
    lText.append('name = "clk_launch"')
    lText.append('period = 10')
    lText.append('[[clock]]')
    lText.append('name = "clk_capture"')
    lText.append('period = 40')
    lText.append(f'port = "{sClockPort}"')
    for sPortName in lPortNames:
        lText.append('')
        lText.append('[[port]]')
        lText.append(f'name = "{sPortName}"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_launch", setup_edge = 4, hold_edge = 4}')
        lText.append('capture_clock = {name = "clk_capture", setup_edge = "C", hold_edge = "A"}')
        lText.append('registers = ["q_spi_output_data_reg"]')
        lText.append(f'timing_reports = ["{sMissingTimingReport}"]')
    return '\n'.join(lText) + '\n'


def find_port_names(lTraces, sClockPort):
    # Without an explicit port order, every trace except the clock is a port, in trace order.
    lPortNames = []
    for sTrace in lTraces:
        sDevicePin = sTrace.split('device_pin = "')[1].split('"')[0]
        if sDevicePin != sClockPort:
            lPortNames.append(sDevicePin)
    return lPortNames


def build_part_text(sPartNumber, sPinName='SDIN'):
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
    lText.append(f'name = "{sPinName}"')
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


def bidirectional_trace(sName, sDevicePin, sPartPin):
    lText = []
    lText.append(output_trace(sName, sDevicePin, sPartPin))
    lText.append('part_to_device = {max_delay = 3.00, min_delay = 1.00}')
    return '\n'.join(lText)


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
    lTraces.append(bidirectional_trace('data', 'IO_DAC_DATA', 'SDIO'))
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

    def run_visualize_block_diagram(self, lTraces, sPartNumber='DAC81404', sClockPort='O_DAC_SCLK', lPortNames=None, sPinName='SDIN'):
        if lPortNames is None:
            lPortNames = find_port_names(lTraces, sClockPort)
        self.write_file('interface.toml', build_interface_text(lPortNames, self.sMissingTimingReport, sClockPort))
        return self.run_with_interface_written(lTraces, sPartNumber, sPinName)

    def run_with_interface_written(self, lTraces, sPartNumber='DAC81404', sPinName='SDIN'):
        self.write_file('part.toml', build_part_text(sPartNumber, sPinName))
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
        lExpected.append('---------------+                       +------------')
        lExpected.append('  Device       |                       |  DAC81404')
        lExpected.append('               |                       |')
        lExpected.append('  O_DAC_DATA  [X] --- data_output --> [X] SDIN')
        lExpected.append('               |                       |')
        lExpected.append('  O_DAC_CSF   [X] --- chip_select --> [X] CSF')
        lExpected.append('               |                       |')
        lExpected.append('  I_DAC_DATA  [X] <-- data_input ---- [X] SDO')
        lExpected.append('               |                       |')
        lExpected.append('  IO_DAC_DATA [X] <-- data ---------> [X] SDIO')
        lExpected.append('               |                       |')
        lExpected.append('  O_DAC_SCLK  [X] --- clock --------> [X] SCLK')
        lExpected.append('               |                       |')
        lExpected.append('---------------+                       +------------')
        self.assert_rows_drawn(lExpected)


class TestVisualizeBlockDiagramWidths(BlockDiagramTestCase):

    def test_widens_the_device_for_a_longer_port_name(self):
        lTraces = []
        lTraces.append(output_trace('data_output', 'O_DATA_LONGER_NAME', 'SDIN'))
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        self.run_visualize_block_diagram(lTraces)
        lExpected = []
        lExpected.append('-' * 22 + '+' + ' ' * 23 + '+' + '-' * 12)
        lExpected.append('  Device' + ' ' * 14 + '|' + ' ' * 23 + '|  DAC81404')
        lExpected.append(' ' * 22 + '|' + ' ' * 23 + '|')
        lExpected.append('  O_DATA_LONGER_NAME [X] --- data_output --> [X] SDIN')
        lExpected.append(' ' * 22 + '|' + ' ' * 23 + '|')
        lExpected.append('  O_DAC_SCLK' + ' ' * 9 + '[X] --- clock --------> [X] SCLK')
        lExpected.append(' ' * 22 + '|' + ' ' * 23 + '|')
        lExpected.append('-' * 22 + '+' + ' ' * 23 + '+' + '-' * 12)
        self.assert_rows_drawn(lExpected)

    def test_lengthens_every_arrow_for_a_longer_trace_name(self):
        lTraces = []
        lTraces.append(output_trace('serial_data_output', 'O_DAC_DATA', 'SDIN'))
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        self.run_visualize_block_diagram(lTraces)
        lExpected = []
        lExpected.append('-' * 14 + '+' + ' ' * 30 + '+' + '-' * 12)
        lExpected.append('  Device      |' + ' ' * 30 + '|  DAC81404')
        lExpected.append(' ' * 14 + '|' + ' ' * 30 + '|')
        lExpected.append('  O_DAC_DATA [X] --- serial_data_output --> [X] SDIN')
        lExpected.append(' ' * 14 + '|' + ' ' * 30 + '|')
        lExpected.append('  O_DAC_SCLK [X] --- clock ' + '-' * 15 + '> [X] SCLK')
        lExpected.append(' ' * 14 + '|' + ' ' * 30 + '|')
        lExpected.append('-' * 14 + '+' + ' ' * 30 + '+' + '-' * 12)
        self.assert_rows_drawn(lExpected)

    def test_widens_the_part_for_a_longer_part_number(self):
        lTraces = []
        lTraces.append(output_trace('data_output', 'O_DAC_DATA', 'SDIN'))
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        self.run_visualize_block_diagram(lTraces, 'ADC128S102')
        lExpected = []
        lExpected.append('-' * 14 + '+' + ' ' * 23 + '+' + '-' * 14)
        lExpected.append('  Device      |' + ' ' * 23 + '|  ADC128S102')
        self.assert_rows_drawn(lExpected)

    def test_widens_the_part_for_a_pin_name_longer_than_the_part_number(self):
        lTraces = []
        lTraces.append(output_trace('data_output', 'O_DAC_DATA', 'SDIN_LONG_NAME'))
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        self.run_visualize_block_diagram(lTraces, 'DAC1', sPinName='SDIN_LONG_NAME')
        lExpected = []
        lExpected.append('-' * 14 + '+' + ' ' * 23 + '+' + '-' * 18)
        lExpected.append('  Device      |' + ' ' * 23 + '|  DAC1')
        lExpected.append(' ' * 14 + '|' + ' ' * 23 + '|')
        lExpected.append('  O_DAC_DATA [X] --- data_output --> [X] SDIN_LONG_NAME')
        self.assert_rows_drawn(lExpected)

    def test_keeps_the_device_wide_enough_for_its_label(self):
        lTraces = []
        lTraces.append(output_trace('d', 'D', 'SDIN'))
        lTraces.append(output_trace('c', 'C', 'SCLK'))
        self.run_visualize_block_diagram(lTraces, sClockPort='C')
        lExpected = []
        lExpected.append('-' * 10 + '+' + ' ' * 13 + '+' + '-' * 12)
        lExpected.append('  Device  |' + ' ' * 13 + '|  DAC81404')
        lExpected.append(' ' * 10 + '|' + ' ' * 13 + '|')
        lExpected.append('  D      [X] --- d --> [X] SDIN')
        lExpected.append(' ' * 10 + '|' + ' ' * 13 + '|')
        lExpected.append('  C      [X] --- c --> [X] SCLK')
        lExpected.append(' ' * 10 + '|' + ' ' * 13 + '|')
        lExpected.append('-' * 10 + '+' + ' ' * 13 + '+' + '-' * 12)
        self.assert_rows_drawn(lExpected)


class TestVisualizeBlockDiagramRowOrder(BlockDiagramTestCase):

    def assert_trace_rows_in_order(self, lExpectedTraceRows):
        lTraceRows = []
        for sLine in self.oStdout.getvalue().split('\n'):
            if '[X]' in sLine:
                lTraceRows.append(sLine)
        self.assertEqual(lExpectedTraceRows, lTraceRows)

    def test_draws_rows_in_the_order_of_the_interface_ports(self):
        lPortNames = ['I_DAC_DATA', 'O_DAC_DATA', 'O_DAC_CSF']
        self.run_visualize_block_diagram(build_dac81404_traces(), lPortNames=lPortNames)
        lExpected = []
        lExpected.append('  I_DAC_DATA [X] <-- data_input ---- [X] SDO')
        lExpected.append('  O_DAC_DATA [X] --- data_output --> [X] SDIN')
        lExpected.append('  O_DAC_CSF  [X] --- chip_select --> [X] CSF')
        lExpected.append('  O_DAC_SCLK [X] --- clock --------> [X] SCLK')
        self.assert_trace_rows_in_order(lExpected)

    def test_draws_the_clock_last_when_it_comes_first_in_the_traces(self):
        lTraces = []
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        lTraces.append(output_trace('data_output', 'O_DAC_DATA', 'SDIN'))
        self.run_visualize_block_diagram(lTraces)
        lExpected = []
        lExpected.append('  O_DAC_DATA [X] --- data_output --> [X] SDIN')
        lExpected.append('  O_DAC_SCLK [X] --- clock --------> [X] SCLK')
        self.assert_trace_rows_in_order(lExpected)

    def test_leaves_out_a_trace_that_no_port_names(self):
        lTraces = []
        lTraces.append(output_trace('data_output', 'O_DAC_DATA', 'SDIN'))
        lTraces.append(output_trace('chip_select_with_a_long_name', 'O_DAC_CSF', 'CSF'))
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        self.run_visualize_block_diagram(lTraces, lPortNames=['O_DAC_DATA'])
        lExpected = []
        lExpected.append('  O_DAC_DATA [X] --- data_output --> [X] SDIN')
        lExpected.append('  O_DAC_SCLK [X] --- clock --------> [X] SCLK')
        self.assert_trace_rows_in_order(lExpected)


class TestVisualizeBlockDiagramDirections(BlockDiagramTestCase):

    def test_draws_both_arrow_heads_for_a_trace_in_both_directions(self):
        lTraces = []
        lTraces.append(output_trace('data_output', 'O_DAC_DATA', 'SDIN'))
        lTraces.append(bidirectional_trace('data', 'IO_DAC_DATA', 'SDIO'))
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        self.run_visualize_block_diagram(lTraces)
        self.assert_rows_drawn(['  IO_DAC_DATA [X] <-- data ---------> [X] SDIO'])


class TestVisualizeBlockDiagramClocks(BlockDiagramTestCase):

    def test_draws_a_row_for_each_capture_clock_after_the_data_rows(self):
        lText = []
        lText.append('description = "two capture clocks"')
        lText.append('name = "SPI_PAIR"')
        lText.append('part = "part.toml"')
        lText.append('part_interface = "Serial Interface"')
        lText.append('traces = "traces.toml"')
        lText.append('[[clock]]')
        lText.append('name = "clk_launch"')
        lText.append('period = 10')
        lText.append('[[clock]]')
        lText.append('name = "dac_sclk"')
        lText.append('period = 40')
        lText.append('port = "O_DAC_SCLK"')
        lText.append('[[clock]]')
        lText.append('name = "adc_sclk"')
        lText.append('period = 40')
        lText.append('port = "O_ADC_SCLK"')
        for sPortName, sCaptureClock in [('O_DAC_DATA', 'dac_sclk'), ('O_ADC_DATA', 'adc_sclk')]:
            lText.append('[[port]]')
            lText.append(f'name = "{sPortName}"')
            lText.append('methodology = "SDR-SS-O"')
            lText.append('launch_clock = {name = "clk_launch", setup_edge = 4, hold_edge = 4}')
            lText.append(f'capture_clock = {{name = "{sCaptureClock}", setup_edge = "C", hold_edge = "A"}}')
            lText.append('registers = ["q_spi_output_data_reg"]')
            lText.append(f'timing_reports = ["{self.sMissingTimingReport}"]')
        self.write_file('interface.toml', '\n'.join(lText) + '\n')
        lTraces = []
        lTraces.append(output_trace('dac_clock', 'O_DAC_SCLK', 'SCLK'))
        lTraces.append(output_trace('dac_data', 'O_DAC_DATA', 'SDIN'))
        lTraces.append(output_trace('adc_clock', 'O_ADC_SCLK', 'SCLK'))
        lTraces.append(output_trace('adc_data', 'O_ADC_DATA', 'SDIN'))
        self.run_with_interface_written(lTraces)
        lTraceRows = []
        for sLine in self.oStdout.getvalue().split('\n'):
            if '[X]' in sLine:
                lTraceRows.append(sLine)
        lExpected = []
        lExpected.append('  O_DAC_DATA [X] --- dac_data ---> [X] SDIN')
        lExpected.append('  O_ADC_DATA [X] --- adc_data ---> [X] SDIN')
        lExpected.append('  O_DAC_SCLK [X] --- dac_clock --> [X] SCLK')
        lExpected.append('  O_ADC_SCLK [X] --- adc_clock --> [X] SCLK')
        self.assertEqual(lExpected, lTraceRows)


class TestVisualizeBlockDiagramErrors(BlockDiagramTestCase):

    def test_reports_a_traces_error(self):
        lTraces = []
        lTraces.append(output_trace('data_output', 'O_DAC_DATA', 'SDIN').replace('{max_delay = 3.00, min_delay = 1.00}', '{}'))
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        self.assertEqual(2, self.run_visualize_block_diagram(lTraces))
        self.assertRegex(self.oStderr.getvalue(), r'^ERROR: \[traces_config_005\] ')


class TestVisualizeBlockDiagramDeferredPorts(BlockDiagramTestCase):

    def test_draws_the_trace_of_a_deferred_port(self):
        lTraces = build_dac81404_traces()
        self.write_file('interface.toml', build_interface_text(['O_DAC_DATA'], self.sMissingTimingReport, 'O_DAC_SCLK') + '\n[[port]]\nname = "O_DAC_CSF"\nstatus = "defer"\n')
        self.assertEqual(0, self.run_with_interface_written(lTraces))
        lTraceRows = []
        for sLine in self.oStdout.getvalue().split('\n'):
            if '[X]' in sLine:
                lTraceRows.append(sLine)
        lExpected = []
        lExpected.append('  O_DAC_DATA [X] --- data_output --> [X] SDIN')
        lExpected.append('  O_DAC_CSF  [X] --- chip_select --> [X] CSF')
        lExpected.append('  O_DAC_SCLK [X] --- clock --------> [X] SCLK')
        self.assertEqual(lExpected, lTraceRows)

