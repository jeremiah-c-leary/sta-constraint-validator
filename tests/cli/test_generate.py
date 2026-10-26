import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__


GENERATOR = '{source = "q_sclk_reg", master_pin = "C", target_pin = "Q"}'


def build_interface_text(lPorts, sMissingTimingReport):
    lText = []
    lText.append('description = "generate test"')
    lText.append('interface = "DAC_SPI_1"')
    lText.append('part = "part.toml"')
    lText.append('traces = "traces.toml"')
    for sPort in lPorts:
        lText.append('')
        lText.append(sPort)
        lText.append(f'timing_reports = ["{sMissingTimingReport}"]')
    return '\n'.join(lText) + '\n'


def build_port_text(sName, fLaunchPeriod, fCapturePeriod, lSetupEdges, lHoldEdges, sGenerator=GENERATOR):
    lText = []
    lText.append('[[port]]')
    lText.append(f'name = "{sName}"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append(f'launch_clock = {{name = "clk_launch", period = {fLaunchPeriod}, setup_edge = {lSetupEdges[0]}, hold_edge = {lHoldEdges[0]}}}')
    lText.append(f'capture_clock = {{port = "O_SCLK", name = "clk_capture", period = {fCapturePeriod}, {build_generator_text(sGenerator)}setup_edge = "{lSetupEdges[1]}", hold_edge = "{lHoldEdges[1]}"}}')
    return '\n'.join(lText)


def build_generator_text(sGenerator):
    if sGenerator is None:
        return ''
    return f'generator = {sGenerator}, '


def build_part_text():
    lText = []
    lText.append('[properties]')
    lText.append('manufacturer = "Texas Instruments"')
    lText.append('part_number = "DAC81404"')
    lText.append('')
    lText.append('[datasheet]')
    lText.append('name = "DAC81404"')
    lText.append('url = "https://www.ti.com/lit/ds/symlink/dac81404.pdf"')
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
    lText.append('setup = {value = 7, symbol = "tSDIS", source = "Table 7.6"}')
    lText.append('hold = {value = 2, symbol = "tSDIH", source = "Table 7.6"}')
    return '\n'.join(lText) + '\n'


def build_traces_text(lPortNames):
    lText = []
    for sPortName in lPortNames:
        lText.append('[[trace]]')
        lText.append(f'name = "{sPortName}_data"')
        lText.append(f'device_pin = "{sPortName}"')
        lText.append('part_pin = "SDIN"')
        lText.append('device_to_part = {max_delay = 1.5, min_delay = 0.5}')
        lText.append('')
    lText.append('[[trace]]')
    lText.append('name = "clock"')
    lText.append('device_pin = "O_SCLK"')
    lText.append('part_pin = "SCLK"')
    lText.append('device_to_part = {max_delay = 1.2, min_delay = 0.4}')
    return '\n'.join(lText) + '\n'


class GenerateTestCase(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        self.sInterfaceFile = os.path.join(self.sDirectory, 'interface.toml')
        self.sMissingTimingReport = os.path.join(self.sDirectory, 'not_written_yet.rpt')
        self.write_file('part.toml', build_part_text())
        self.write_file('traces.toml', build_traces_text(['O_DATA', 'O_CHIP_SELECT']))

    def write_file(self, sFilename, sText):
        with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
            oFile.write(sText)

    def run_generate_xdc(self, lPorts):
        self.write_file('interface.toml', build_interface_text(lPorts, self.sMissingTimingReport))
        lArgv = ['stacv', 'generate', 'xdc', self.sInterfaceFile]
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', lArgv):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def get_output_lines(self):
        return self.oStdout.getvalue().split('\n')

    def assert_line_written(self, sExpectedLine):
        self.assertIn(sExpectedLine, self.get_output_lines())

    def count_lines_starting_with(self, sStartOfLine):
        iCount = 0
        for sLine in self.get_output_lines():
            if sLine.startswith(sStartOfLine):
                iCount += 1
        return iCount

    def assert_line_not_written(self, sStartOfLine):
        for sLine in self.get_output_lines():
            self.assertFalse(sLine.startswith(sStartOfLine), sLine)


class TestGenerateXdcDispatch(GenerateTestCase):

    def test_exits_with_zero_when_timing_reports_do_not_exist(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.assertEqual(0, self.run_generate_xdc([sPort]))

    def test_writes_nothing_to_stderr(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.run_generate_xdc([sPort])
        self.assertEqual('', self.oStderr.getvalue())

    def test_exits_with_two_on_interface_error(self):
        self.assertEqual(2, self.run_generate_xdc([]))

    def test_interface_error_is_written_to_stderr(self):
        self.run_generate_xdc([])
        self.assertRegex(self.oStderr.getvalue(), r'^ERROR: \[interface_config_002\] ')


class TestGenerateXdcGeneratedClock(GenerateTestCase):

    def test_divides_the_capture_clock_from_the_generator_when_it_is_slower(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.run_generate_xdc([sPort])
        self.assert_line_written('create_generated_clock -name clk_capture -source [get_pins q_sclk_reg/C] -divide_by 4 [get_pins q_sclk_reg/Q]')

    def test_multiplies_the_capture_clock_from_the_generator_when_it_is_faster(self):
        sPort = build_port_text('O_DATA', 40, 10, [2, 'K'], [2, 'I'])
        self.run_generate_xdc([sPort])
        self.assert_line_written('create_generated_clock -name clk_capture -source [get_pins q_sclk_reg/C] -multiply_by 4 [get_pins q_sclk_reg/Q]')

    def test_divides_by_one_when_the_periods_are_equal(self):
        sPort = build_port_text('O_DATA', 10, 10, [0, 'C'], [0, 'A'])
        self.run_generate_xdc([sPort])
        self.assert_line_written('create_generated_clock -name clk_capture -source [get_pins q_sclk_reg/C] -divide_by 1 [get_pins q_sclk_reg/Q]')

    def test_uses_the_pins_named_by_the_generator(self):
        sGenerator = '{source = "u_clock_out/oddr_inst", master_pin = "CLK", target_pin = "OUT"}'
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'], sGenerator)
        self.run_generate_xdc([sPort])
        self.assert_line_written('create_generated_clock -name clk_capture -source [get_pins u_clock_out/oddr_inst/CLK] -divide_by 4 [get_pins u_clock_out/oddr_inst/OUT]')

    def test_generates_a_capture_clock_shared_by_two_ports_once(self):
        lPorts = []
        lPorts.append(build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A']))
        lPorts.append(build_port_text('O_CHIP_SELECT', 10, 40, [4, 'C'], [4, 'A']))
        self.run_generate_xdc(lPorts)
        self.assertEqual(1, self.count_lines_starting_with('create_generated_clock '))


class TestGenerateXdcOutputDelays(GenerateTestCase):

    def test_writes_the_maximum_output_delay_against_the_clock_port(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.run_generate_xdc([sPort])
        self.assert_line_written('set_output_delay -clock [get_clocks clk_capture] -reference_pin [get_ports O_SCLK] -max 8.100 [get_ports O_DATA]')

    def test_writes_the_minimum_output_delay_against_the_clock_port(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.run_generate_xdc([sPort])
        self.assert_line_written('set_output_delay -clock [get_clocks clk_capture] -reference_pin [get_ports O_SCLK] -min -2.700 [get_ports O_DATA]')

    def test_applies_the_maximum_output_delay_to_a_falling_capture_edge(self):
        sPort = build_port_text('O_DATA', 10, 40, [2, 'B'], [4, 'B'])
        self.run_generate_xdc([sPort])
        self.assert_line_written('set_output_delay -clock [get_clocks clk_capture] -clock_fall -reference_pin [get_ports O_SCLK] -max 8.100 [get_ports O_DATA]')

    def test_applies_the_minimum_output_delay_to_a_falling_capture_edge(self):
        sPort = build_port_text('O_DATA', 10, 40, [2, 'B'], [4, 'B'])
        self.run_generate_xdc([sPort])
        self.assert_line_written('set_output_delay -clock [get_clocks clk_capture] -clock_fall -reference_pin [get_ports O_SCLK] -min -2.700 [get_ports O_DATA]')

    def test_writes_output_delays_for_every_port(self):
        lPorts = []
        lPorts.append(build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A']))
        lPorts.append(build_port_text('O_CHIP_SELECT', 10, 40, [4, 'C'], [4, 'A']))
        self.run_generate_xdc(lPorts)
        self.assert_line_written('set_output_delay -clock [get_clocks clk_capture] -reference_pin [get_ports O_SCLK] -max 8.100 [get_ports O_CHIP_SELECT]')
        self.assert_line_written('set_output_delay -clock [get_clocks clk_capture] -reference_pin [get_ports O_SCLK] -min -2.700 [get_ports O_CHIP_SELECT]')
