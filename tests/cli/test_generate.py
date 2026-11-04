import contextlib
import hashlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__
from stacv import version


GENERATOR = '{source = "q_sclk_reg", master_pin = "C", target_pin = "Q", master_clock = "clk_launch"}'
FIRST_LAST_CLOCK = 'SDR-SS-O-FLC'


DEFERRED_O_DATA = '[[port]]\nstatus = "defer"\nname = "O_DATA"'

def build_interface_text(lPorts, sMissingTimingReport):
    lText = []
    lText.append('description = "generate test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append('part = "part.toml"')
    lText.append('part_interface = "Serial Interface"')
    lText.append('traces = "traces.toml"')
    for sClocks in find_distinct_clock_tables(lPorts):
        lText.append('')
        lText.append(sClocks)
    for sPort in lPorts:
        lText.append('')
        lText.append(remove_clock_tables(sPort))
        lText.append('registers = ["q_spi_output_data_reg"]')
        lText.append(f'timing_reports = ["{sMissingTimingReport}"]')
    return '\n'.join(lText) + '\n'


def find_distinct_clock_tables(lPorts):
    # Each port text starts with the clock tables it uses; ports sharing clocks write them once.
    lClockTables = []
    for sPort in lPorts:
        sClocks = sPort.split('[[port]]')[0].strip()
        if sClocks not in lClockTables:
            lClockTables.append(sClocks)
    return lClockTables


def remove_clock_tables(sPort):
    return '[[port]]' + sPort.split('[[port]]')[1]


def build_first_last_clock_port_text(sName, fLaunchPeriod, fCapturePeriod, lSetupEdges, lHoldEdges):
    # The setup and hold edges of an SDR-SS-O-FLC port are independent, so it reaches every multicycle the generator can write.
    return build_port_text(sName, fLaunchPeriod, fCapturePeriod, lSetupEdges, lHoldEdges, sMethodology=FIRST_LAST_CLOCK)


def build_port_text(sName, fLaunchPeriod, fCapturePeriod, lSetupEdges, lHoldEdges, sGenerator=GENERATOR, sMethodology='SDR-SS-O'):
    lText = []
    lText.append('[[clock]]')
    lText.append('name = "clk_launch"')
    lText.append(f'period = {fLaunchPeriod}')
    lText.append('[[clock]]')
    lText.append('name = "clk_capture"')
    lText.append(f'period = {fCapturePeriod}')
    lText.append('port = "O_SCLK"')
    if sMethodology == FIRST_LAST_CLOCK:
        lText.append('idle = "low"')
    if sGenerator is not None:
        lText.append(f'generator = {sGenerator}')
    lText.append('[[port]]')
    lText.append(f'name = "{sName}"')
    lText.append(f'methodology = "{sMethodology}"')
    lText.append(f'launch_clock = {{name = "clk_launch", setup_edge = {lSetupEdges[0]}, hold_edge = {lHoldEdges[0]}}}')
    lText.append(f'capture_clock = {{name = "clk_capture", setup_edge = "{lSetupEdges[1]}", hold_edge = "{lHoldEdges[1]}"}}')
    return '\n'.join(lText)


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

    def assert_no_line_contains(self, sText):
        for sLine in self.get_output_lines():
            self.assertNotIn(sText, sLine)


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
        sGenerator = '{source = "u_clock_out/oddr_inst", master_pin = "CLK", target_pin = "OUT", master_clock = "clk_launch"}'
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'], sGenerator)
        self.run_generate_xdc([sPort])
        self.assert_line_written('create_generated_clock -name clk_capture -source [get_pins u_clock_out/oddr_inst/CLK] -divide_by 4 [get_pins u_clock_out/oddr_inst/OUT]')

    def test_generates_a_capture_clock_shared_by_two_ports_once(self):
        lPorts = []
        lPorts.append(build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A']))
        lPorts.append(build_port_text('O_CHIP_SELECT', 10, 40, [4, 'C'], [4, 'A']))
        self.run_generate_xdc(lPorts)
        self.assertEqual(1, self.count_lines_starting_with('create_generated_clock '))


    def test_divides_by_the_period_of_the_master_clock(self):
        sGenerator = '{source = "q_sclk_reg", master_pin = "C", target_pin = "Q", master_clock = "clk_master"}'
        sMasterClock = '[[clock]]\nname = "clk_master"\nperiod = 20\n'
        sPort = sMasterClock + build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'], sGenerator)
        self.run_generate_xdc([sPort])
        self.assert_line_written('create_generated_clock -name clk_capture -source [get_pins q_sclk_reg/C] -divide_by 2 [get_pins q_sclk_reg/Q]')


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
        sPort = build_first_last_clock_port_text('O_DATA', 10, 40, [2, 'B'], [4, 'B'])
        self.run_generate_xdc([sPort])
        self.assert_line_written('set_output_delay -clock [get_clocks clk_capture] -clock_fall -reference_pin [get_ports O_SCLK] -max 8.100 [get_ports O_DATA]')

    def test_applies_the_minimum_output_delay_to_a_falling_capture_edge(self):
        sPort = build_first_last_clock_port_text('O_DATA', 10, 40, [2, 'B'], [4, 'B'])
        self.run_generate_xdc([sPort])
        self.assert_line_written('set_output_delay -clock [get_clocks clk_capture] -clock_fall -reference_pin [get_ports O_SCLK] -min -2.700 [get_ports O_DATA]')

    def test_writes_output_delays_for_every_port(self):
        lPorts = []
        lPorts.append(build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A']))
        lPorts.append(build_port_text('O_CHIP_SELECT', 10, 40, [4, 'C'], [4, 'A']))
        self.run_generate_xdc(lPorts)
        self.assert_line_written('set_output_delay -clock [get_clocks clk_capture] -reference_pin [get_ports O_SCLK] -max 8.100 [get_ports O_CHIP_SELECT]')
        self.assert_line_written('set_output_delay -clock [get_clocks clk_capture] -reference_pin [get_ports O_SCLK] -min -2.700 [get_ports O_CHIP_SELECT]')


class TestGenerateXdcSetupMulticycle(GenerateTestCase):

    def test_moves_the_launch_edge_when_the_launch_clock_is_faster(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.run_generate_xdc([sPort])
        self.assert_line_written('set_multicycle_path 2 -setup -start -from [get_clocks clk_launch] -to [get_ports O_DATA]')

    def test_moves_the_capture_edge_when_the_capture_clock_is_faster(self):
        sPort = build_port_text('O_DATA', 40, 10, [0, 'E'], [0, 'C'])
        self.run_generate_xdc([sPort])
        self.assert_line_written('set_multicycle_path 2 -setup -end -from [get_clocks clk_launch] -to [get_ports O_DATA]')

    def test_moves_the_capture_edge_when_the_periods_are_equal(self):
        sPort = build_port_text('O_DATA', 10, 10, [0, 'E'], [0, 'C'])
        self.run_generate_xdc([sPort])
        self.assert_line_written('set_multicycle_path 2 -setup -end -from [get_clocks clk_launch] -to [get_ports O_DATA]')

    def test_writes_no_setup_multicycle_of_one(self):
        sPort = build_port_text('O_DATA', 10, 40, [6, 'C'], [6, 'A'])
        self.run_generate_xdc([sPort])
        self.assert_no_line_contains(' -setup ')

    def test_writes_a_setup_multicycle_for_every_port(self):
        lPorts = []
        lPorts.append(build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A']))
        lPorts.append(build_port_text('O_CHIP_SELECT', 10, 40, [2, 'C'], [2, 'A']))
        self.run_generate_xdc(lPorts)
        self.assert_line_written('set_multicycle_path 2 -setup -start -from [get_clocks clk_launch] -to [get_ports O_DATA]')
        self.assert_line_written('set_multicycle_path 3 -setup -start -from [get_clocks clk_launch] -to [get_ports O_CHIP_SELECT]')


class TestGenerateXdcHoldMulticycle(GenerateTestCase):

    def test_moves_the_hold_launch_edge_when_the_launch_clock_is_faster(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.run_generate_xdc([sPort])
        self.assert_line_written('set_multicycle_path 3 -hold -start -from [get_clocks clk_launch] -to [get_ports O_DATA]')

    def test_moves_the_hold_capture_edge_when_the_capture_clock_is_faster(self):
        sPort = build_first_last_clock_port_text('O_DATA', 40, 10, [0, 'E'], [0, 'A'])
        self.run_generate_xdc([sPort])
        self.assert_line_written('set_multicycle_path 1 -hold -end -from [get_clocks clk_launch] -to [get_ports O_DATA]')

    def test_writes_no_hold_multicycle_of_zero(self):
        sPort = build_first_last_clock_port_text('O_DATA', 10, 40, [6, 'C'], [8, 'C'])
        self.run_generate_xdc([sPort])
        self.assert_no_line_contains(' -hold ')

    def test_writes_a_hold_multicycle_for_every_port(self):
        lPorts = []
        # Both ports are SDR-SS-O-FLC, so they share one clock table.
        lPorts.append(build_first_last_clock_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A']))
        lPorts.append(build_first_last_clock_port_text('O_CHIP_SELECT', 10, 40, [2, 'C'], [4, 'A']))
        self.run_generate_xdc(lPorts)
        self.assert_line_written('set_multicycle_path 3 -hold -start -from [get_clocks clk_launch] -to [get_ports O_DATA]')
        self.assert_line_written('set_multicycle_path 4 -hold -start -from [get_clocks clk_launch] -to [get_ports O_CHIP_SELECT]')


class TestGenerateXdcErrors(GenerateTestCase):

    def assert_error_written(self, sIdentifier):
        self.assertRegex(self.oStderr.getvalue(), r'^ERROR: \[' + sIdentifier + r'\] ')

    def test_exits_with_two_on_a_generate_error(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'], None)
        self.assertEqual(2, self.run_generate_xdc([sPort]))

    def test_writes_no_constraints_on_a_generate_error(self):
        lPorts = []
        # Both ports are SDR-SS-O-FLC, so they share one clock table.
        lPorts.append(build_first_last_clock_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A']))
        lPorts.append(build_first_last_clock_port_text('O_CHIP_SELECT', 10, 40, [10, 'C'], [4, 'A']))
        self.run_generate_xdc(lPorts)
        self.assertRegex(self.oStderr.getvalue(), r'^ERROR: \[generate_004\] ')
        self.assertEqual('', self.oStdout.getvalue())

    def test_reports_a_capture_clock_without_a_generator(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'], None)
        self.run_generate_xdc([sPort])
        self.assert_error_written('generate_001')

    def test_reports_a_setup_requirement_that_is_not_a_whole_number_of_step_periods(self):
        sPort = build_first_last_clock_port_text('O_DATA', 10, 40, [3, 'C'], [4, 'A'])
        self.run_generate_xdc([sPort])
        self.assert_error_written('generate_002')

    def test_reports_a_hold_requirement_that_is_not_a_whole_number_of_step_periods(self):
        sPort = build_first_last_clock_port_text('O_DATA', 10, 40, [4, 'C'], [3, 'A'])
        self.run_generate_xdc([sPort])
        self.assert_error_written('generate_003')

    def test_reports_a_setup_multicycle_less_than_zero(self):
        # Launch edge 10 at 50 ns is after capture edge C at 40 ns.
        sPort = build_first_last_clock_port_text('O_DATA', 10, 40, [10, 'C'], [4, 'A'])
        self.run_generate_xdc([sPort])
        self.assert_error_written('generate_004')

    def test_reports_a_hold_multicycle_less_than_zero(self):
        sPort = build_first_last_clock_port_text('O_DATA', 10, 40, [6, 'C'], [6, 'C'])
        self.run_generate_xdc([sPort])
        self.assert_error_written('generate_005')

    def test_reports_setup_and_hold_capture_edges_of_different_types(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [2, 'B'])
        self.run_generate_xdc([sPort])
        self.assert_error_written('interface_config_018')


class TestGenerateXdcInputErrors(GenerateTestCase):

    def assert_error_written(self, sIdentifier):
        self.assertRegex(self.oStderr.getvalue(), r'^ERROR: \[' + sIdentifier + r'\] ')

    def write_traces(self, lTraces):
        lText = []
        for sDevicePin, sPartPin in lTraces:
            lText.append('[[trace]]')
            lText.append(f'name = "{sDevicePin}_trace"')
            lText.append(f'device_pin = "{sDevicePin}"')
            lText.append(f'part_pin = "{sPartPin}"')
            lText.append('device_to_part = {max_delay = 1.5, min_delay = 0.5}')
            lText.append('')
        self.write_file('traces.toml', '\n'.join(lText))

    def test_reports_a_port_without_a_trace(self):
        # The part's SDIN has a trace to O_DATA, which is deferred, so only O_NO_TRACE has no trace.
        sPort = build_port_text('O_NO_TRACE', 10, 40, [4, 'C'], [4, 'A'])
        self.assertEqual(2, self.run_generate_xdc([sPort, DEFERRED_O_DATA]))
        self.assert_error_written('generate_007')

    def test_reports_a_trace_to_a_pin_the_part_does_not_have(self):
        # SDIN has its own trace to a deferred port, so only the trace of O_DATA reaches a pin the part does not have.
        self.write_traces([('O_DATA', 'SDIN_UNKNOWN'), ('O_SPARE', 'SDIN'), ('O_SCLK', 'SCLK')])
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.assertEqual(2, self.run_generate_xdc([sPort, '[[port]]\nstatus = "defer"\nname = "O_SPARE"']))
        self.assert_error_written('generate_008')

    def test_reports_a_missing_clock_trace(self):
        self.write_traces([('O_DATA', 'SDIN'), ('O_OTHER_SCLK', 'SCLK')])
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.assertEqual(2, self.run_generate_xdc([sPort]))
        self.assert_error_written('generate_009')

    def test_reports_a_traces_error(self):
        self.write_file('traces.toml', '[[trace]]\nname = "O_DATA_trace"\ndevice_pin = "O_DATA"\npart_pin = "SDIN"\ndevice_to_part = {}\n')
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.assertEqual(2, self.run_generate_xdc([sPort]))
        self.assert_error_written('traces_config_005')


class TestGenerateXdcDeferredPorts(GenerateTestCase):

    def test_writes_nothing_for_a_deferred_port(self):
        lPorts = []
        lPorts.append(build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A']))
        lPorts.append('[[port]]\nname = "O_NO_TRACE"\nstatus = "defer"')
        self.assertEqual(0, self.run_generate_xdc(lPorts))
        for sLine in self.get_output_lines():
            if not sLine.startswith('#'):
                self.assertNotIn('O_NO_TRACE', sLine)
        self.assert_line_written('set_output_delay -clock [get_clocks clk_capture] -reference_pin [get_ports O_SCLK] -max 8.100 [get_ports O_DATA]')


BANNER = '#' * 79


class XdcFileTestCase(GenerateTestCase):

    def run_with_a_deferred_port(self):
        lPorts = []
        lPorts.append(build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A']))
        lPorts.append('[[port]]\nname = "O_CHIP_SELECT"\nstatus = "defer"')
        self.run_generate_xdc(lPorts)

    def read_section(self, sTitle):
        lLines = self.get_output_lines()
        iStart = lLines.index(f'#  Section {sTitle}') + 2
        # The newline that ends the file leaves an empty last element.
        iEnd = len(lLines) - 1
        for iLine in range(iStart, len(lLines)):
            if lLines[iLine] == BANNER:
                iEnd = iLine
                break
        return lLines[iStart:iEnd]


    def assert_lines_in_section(self, sTitle, lExpected):
        lSection = self.read_section(sTitle)
        for iStart in range(len(lSection) - len(lExpected) + 1):
            if lSection[iStart:iStart + len(lExpected)] == lExpected:
                return
        self.fail('\n'.join(['Lines not found in section:'] + lExpected + ['Section:'] + lSection))

class TestGenerateXdcLayout(XdcFileTestCase):

    def test_starts_with_a_header_naming_the_interface_and_the_stacv_version(self):
        self.run_with_a_deferred_port()
        lExpected = []
        lExpected.append(BANNER)
        lExpected.append('#  DAC_SPI_1')
        lExpected.append(BANNER)
        lExpected.append('#')
        lExpected.append('# This file is a timing constraints file for the DAC_SPI_1 interface.')
        lExpected.append(f'# Generated by stacv version {version.VERSION}')
        lExpected.append('#')
        self.assertEqual(lExpected, self.get_output_lines()[0:7])

    def test_lists_every_section_in_the_table_of_contents(self):
        self.run_with_a_deferred_port()
        lExpected = []
        lExpected.append('#  Table of contents')
        lExpected.append('#')
        lExpected.append('#    Section 1:  References')
        lExpected.append('#    Section 2:  Block Diagram')
        lExpected.append('#    Section 3:  Inputs')
        lExpected.append('#    Section 3.1:  Trace Delays')
        lExpected.append('#    Section 3.2:  Part Timing')
        lExpected.append('#    Section 4:  Clocks')
        lExpected.append('#    Section 4.1:  clk_capture Generated Clock')
        lExpected.append('#    Section 5:  Ports')
        lExpected.append('#    Section 5.1:  O_DATA')
        lExpected.append('#    Section 5.2:  O_CHIP_SELECT')
        lExpected.append('#')
        self.assertEqual(lExpected, self.get_output_lines()[7:20])

    def test_gives_each_section_without_subsections_a_banner_in_order(self):
        self.run_with_a_deferred_port()
        lTitles = []
        lLines = self.get_output_lines()
        for iLine in range(1, len(lLines) - 1):
            if lLines[iLine - 1] == BANNER and lLines[iLine + 1] == BANNER and lLines[iLine].startswith('#  Section'):
                lTitles.append(lLines[iLine])
        lExpected = []
        lExpected.append('#  Section 1:  References')
        lExpected.append('#  Section 2:  Block Diagram')
        lExpected.append('#  Section 3.1:  Trace Delays')
        lExpected.append('#  Section 3.2:  Part Timing')
        lExpected.append('#  Section 4.1:  clk_capture Generated Clock')
        lExpected.append('#  Section 5.1:  O_DATA')
        lExpected.append('#  Section 5.2:  O_CHIP_SELECT')
        self.assertEqual(lExpected, lTitles)

    def test_writes_the_generated_clock_in_its_section(self):
        self.run_with_a_deferred_port()
        lLines = self.get_output_lines()
        iSection = lLines.index('#  Section 4.1:  clk_capture Generated Clock')
        iNextSection = lLines.index('#  Section 5.1:  O_DATA')
        self.assertIn('create_generated_clock -name clk_capture -source [get_pins q_sclk_reg/C] -divide_by 4 [get_pins q_sclk_reg/Q]', lLines[iSection:iNextSection])

    def test_writes_the_port_constraints_in_the_port_section(self):
        self.run_with_a_deferred_port()
        lLines = self.get_output_lines()
        iSection = lLines.index('#  Section 5.1:  O_DATA')
        iNextSection = lLines.index('#  Section 5.2:  O_CHIP_SELECT')
        self.assertIn('set_output_delay -clock [get_clocks clk_capture] -reference_pin [get_ports O_SCLK] -max 8.100 [get_ports O_DATA]', lLines[iSection:iNextSection])

class TestGenerateXdcReferences(XdcFileTestCase):

    def calculate_md5sum(self, sFilename):
        with open(sFilename, 'rb') as oFile:
            return hashlib.file_digest(oFile, 'md5').hexdigest()

    def test_lists_the_input_files_and_the_part_datasheet(self):
        self.run_with_a_deferred_port()
        lFiles = []
        lFiles.append(self.sInterfaceFile)
        lFiles.append(os.path.join(self.sDirectory, 'part.toml'))
        lFiles.append(os.path.join(self.sDirectory, 'traces.toml'))
        iFileColumnWidth = 8
        for sFile in lFiles:
            iFileColumnWidth = max(iFileColumnWidth, len(sFile))
        iFileColumnWidth = min(iFileColumnWidth, 46)
        lExpected = []
        lExpected.append('#')
        lExpected.append('# md5sum                            Filename')
        lExpected.append('# ' + '-' * 32 + '  ' + '-' * iFileColumnWidth)
        for sFile in lFiles:
            lExpected.append(f'# {self.calculate_md5sum(sFile)}  {sFile}')
        lExpected.append('#')
        lExpected.append('# Part:       Texas Instruments DAC81404')
        lExpected.append('# Datasheet:  DAC81404')
        lExpected.append('# Revision:   A')
        lExpected.append('# URL:        https://www.ti.com/lit/ds/symlink/dac81404.pdf')
        lExpected.append('#')
        self.assertEqual(lExpected, self.read_section('1:  References'))


class TestGenerateXdcBlockDiagram(XdcFileTestCase):

    def draw_block_diagram(self):
        oStdout = io.StringIO()
        with mock.patch('sys.argv', ['stacv', 'visualize', 'block_diagram', self.sInterfaceFile]):
            with contextlib.redirect_stdout(oStdout):
                with self.assertRaises(SystemExit):
                    __main__.main()
        return oStdout.getvalue().rstrip('\n').split('\n')

    def test_writes_the_block_diagram_as_comments(self):
        self.run_with_a_deferred_port()
        lExpected = ['#']
        for sLine in self.draw_block_diagram():
            lExpected.append(('# ' + sLine).rstrip())
        lExpected.append('#')
        self.assertEqual(lExpected, self.read_section('2:  Block Diagram'))


class TestGenerateXdcTraceDelays(XdcFileTestCase):

    def test_lists_the_delays_of_every_trace_in_the_block_diagram(self):
        self.run_with_a_deferred_port()
        lExpected = []
        lExpected.append('#')
        lExpected.append('# Trace               From           To    Maximum (ns)  Minimum (ns)  Default')
        lExpected.append('# ------------------  -------------  ----  ------------  ------------  -------')
        lExpected.append('# O_DATA_data         O_DATA         SDIN  1.5           0.5           No')
        lExpected.append('# O_CHIP_SELECT_data  O_CHIP_SELECT  SDIN  1.5           0.5           No')
        lExpected.append('# clock               O_SCLK         SCLK  1.2           0.4           No')
        lExpected.append('#')
        self.assertEqual(lExpected, self.read_section('3.1:  Trace Delays'))

    def test_marks_default_delays_and_lists_each_direction_of_a_trace(self):
        lTraces = []
        lTraces.append('default_delay = {max_delay = 1.0, min_delay = 0.0}')
        lTraces.append('[[trace]]\nname = "O_DATA_data"\ndevice_pin = "O_DATA"\npart_pin = "SDIN"\ndevice_to_part = {max_delay = 1.5, min_delay = 0.5}')
        lTraces.append('[[trace]]\nname = "I_DATA_trace"\ndevice_pin = "I_DATA"\npart_pin = "SDOUT"\npart_to_device = {}')
        lTraces.append('[[trace]]\nname = "IO_DATA_trace"\ndevice_pin = "IO_DATA"\npart_pin = "SDIO"\ndevice_to_part = {}\npart_to_device = {max_delay = 2.5, min_delay = 0.5}')
        lTraces.append('[[trace]]\nname = "clock"\ndevice_pin = "O_SCLK"\npart_pin = "SCLK"\ndevice_to_part = {max_delay = 1.2, min_delay = 0.4}')
        self.write_file('traces.toml', '\n\n'.join(lTraces) + '\n')
        lPorts = []
        lPorts.append(build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A']))
        lPorts.append('[[port]]\nname = "I_DATA"\nstatus = "defer"')
        lPorts.append('[[port]]\nname = "IO_DATA"\nstatus = "defer"')
        self.run_generate_xdc(lPorts)
        lExpected = []
        lExpected.append('#')
        lExpected.append('# Trace          From     To       Maximum (ns)  Minimum (ns)  Default')
        lExpected.append('# -------------  -------  -------  ------------  ------------  -------')
        lExpected.append('# O_DATA_data    O_DATA   SDIN     1.5           0.5           No')
        lExpected.append('# I_DATA_trace   SDOUT    I_DATA   1             0             Yes')
        lExpected.append('# IO_DATA_trace  IO_DATA  SDIO     1             0             Yes')
        lExpected.append('# IO_DATA_trace  SDIO     IO_DATA  2.5           0.5           No')
        lExpected.append('# clock          O_SCLK   SCLK     1.2           0.4           No')
        lExpected.append('#')
        self.assertEqual(lExpected, self.read_section('3.1:  Trace Delays'))


class TestGenerateXdcPartTiming(XdcFileTestCase):

    def test_lists_the_timing_of_each_part_pin_the_traces_reach(self):
        self.run_with_a_deferred_port()
        lExpected = []
        lExpected.append('#')
        lExpected.append('# Pin   Timing  Value (ns)  Symbol  Source')
        lExpected.append('# ----  ------  ----------  ------  ---------')
        lExpected.append('# SDIN  setup   7           tSDIS   Table 7.6')
        lExpected.append('# SDIN  hold    2           tSDIH   Table 7.6')
        lExpected.append('#')
        self.assertEqual(lExpected, self.read_section('3.2:  Part Timing'))

    def test_groups_the_timing_of_each_pin_and_lists_clock_to_out_of_outputs(self):
        sOutputPin = '[[interface.pin]]\nname = "SDO"\nmethodology = "SDR-SS-RT-DO"\nclock = {pin = "SCLK", max_frequency = 12.5}\ncko_max = {value = 30, symbol = "tSDODLY", source = "Table 7.8"}\ncko_min = {value = 0, symbol = "tSDODLY", source = "Table 7.8"}\nlaunch_edge = "Rising"\n'
        self.write_file('part.toml', build_part_text() + '\n' + sOutputPin)
        lTraces = []
        lTraces.append('[[trace]]\nname = "O_DATA_data"\ndevice_pin = "O_DATA"\npart_pin = "SDIN"\ndevice_to_part = {max_delay = 1.5, min_delay = 0.5}')
        lTraces.append('[[trace]]\nname = "I_DATA_data"\ndevice_pin = "I_DATA"\npart_pin = "SDO"\npart_to_device = {max_delay = 1.5, min_delay = 0.5}')
        lTraces.append('[[trace]]\nname = "clock"\ndevice_pin = "O_SCLK"\npart_pin = "SCLK"\ndevice_to_part = {max_delay = 1.2, min_delay = 0.4}')
        self.write_file('traces.toml', '\n\n'.join(lTraces) + '\n')
        lPorts = []
        lPorts.append(build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A']))
        lPorts.append('[[port]]\nname = "I_DATA"\nstatus = "defer"')
        self.run_generate_xdc(lPorts)
        lExpected = []
        lExpected.append('#')
        lExpected.append('# Pin   Timing   Value (ns)  Symbol   Source')
        lExpected.append('# ----  -------  ----------  -------  ---------')
        lExpected.append('# SDIN  setup    7           tSDIS    Table 7.6')
        lExpected.append('# SDIN  hold     2           tSDIH    Table 7.6')
        lExpected.append('#')
        lExpected.append('# SDO   cko_max  30          tSDODLY  Table 7.8')
        lExpected.append('# SDO   cko_min  0           tSDODLY  Table 7.8')
        lExpected.append('#')
        self.assertEqual(lExpected, self.read_section('3.2:  Part Timing'))


class TestGenerateXdcGeneratedClockSection(XdcFileTestCase):

    def test_explains_each_argument_of_a_divided_clock(self):
        self.run_with_a_deferred_port()
        lExpected = []
        lExpected.append('#')
        lExpected.append('# -name:       the name of the generated clock')
        lExpected.append('# -source:     clk_capture is generated by q_sclk_reg, from clk_launch at pin C to pin Q')
        lExpected.append('# -divide_by:  clk_capture period / clk_launch period')
        lExpected.append('#              40 ns / 10 ns')
        lExpected.append('#              4')
        lExpected.append('# objects:     where the generated clock starts')
        lExpected.append('#')
        lExpected.append('')
        lExpected.append('create_generated_clock -name clk_capture -source [get_pins q_sclk_reg/C] -divide_by 4 [get_pins q_sclk_reg/Q]')
        lExpected.append('')
        self.assertEqual(lExpected, self.read_section('4.1:  clk_capture Generated Clock'))

    def test_explains_each_argument_of_a_multiplied_clock(self):
        self.run_generate_xdc([build_port_text('O_DATA', 40, 10, [2, 'K'], [2, 'I'])])
        lExpected = []
        lExpected.append('#')
        lExpected.append('# -name:         the name of the generated clock')
        lExpected.append('# -source:       clk_capture is generated by q_sclk_reg, from clk_launch at pin C to pin Q')
        lExpected.append('# -multiply_by:  clk_launch period / clk_capture period')
        lExpected.append('#                40 ns / 10 ns')
        lExpected.append('#                4')
        lExpected.append('# objects:       where the generated clock starts')
        lExpected.append('#')
        lExpected.append('')
        lExpected.append('create_generated_clock -name clk_capture -source [get_pins q_sclk_reg/C] -multiply_by 4 [get_pins q_sclk_reg/Q]')
        lExpected.append('')
        self.assertEqual(lExpected, self.read_section('4.1:  clk_capture Generated Clock'))


class TestGenerateXdcPortSection(XdcFileTestCase):

    def draw_edges(self):
        oStdout = io.StringIO()
        with mock.patch('sys.argv', ['stacv', 'visualize', 'edges', self.sInterfaceFile]):
            with contextlib.redirect_stdout(oStdout):
                with self.assertRaises(SystemExit):
                    __main__.main()
        lLines = oStdout.getvalue().rstrip('\n').split('\n')
        # The drawing, without the port banner and the requirement lines that follow the capture clock.
        return lLines[4:-4]

    def test_starts_with_the_edges_and_the_requirements_with_their_edges(self):
        self.run_with_a_deferred_port()
        lExpected = ['#']
        for sLine in self.draw_edges():
            lExpected.append(('# ' + sLine).rstrip())
        lExpected.append('#')
        lExpected.append('# setup requirement:  20 ns (launch edge 4 at 20 ns -> capture edge C at 40 ns)')
        lExpected.append('# hold requirement:  -20 ns (launch edge 4 at 20 ns -> capture edge A at 0 ns)')
        lExpected.append('#')
        lExpected.append('#' + '-' * 78)
        self.assertEqual(lExpected, self.read_section('5.1:  O_DATA')[0:len(lExpected)])

    def test_right_aligns_requirements_that_are_not_whole_nanoseconds(self):
        self.run_generate_xdc([build_port_text('O_DATA', 2.5, 20, [2, 'C'], [2, 'A'])])
        lSection = self.read_section('5.1:  O_DATA')
        self.assertIn('# setup requirement:  17.5 ns (launch edge 2 at 2.5 ns -> capture edge C at 20 ns)', lSection)
        self.assertIn('# hold requirement:   -2.5 ns (launch edge 2 at 2.5 ns -> capture edge A at 0 ns)', lSection)

    def test_writes_deferred_for_a_deferred_port(self):
        self.run_with_a_deferred_port()
        self.assertEqual(['#', '# Deferred'], self.read_section('5.2:  O_CHIP_SELECT'))

class TestGenerateXdcOutputDelayComments(XdcFileTestCase):

    def test_explains_each_argument_of_the_maximum_output_delay(self):
        self.run_with_a_deferred_port()
        lExpected = []
        lExpected.append('#')
        lExpected.append('# -clock:                the capture clock')
        lExpected.append('# -reference_pin:        clk_capture is generated at q_sclk_reg/Q.  Without the reference pin,')
        lExpected.append('#                        the delay from Q to O_SCLK is left out of the clock path and the timing')
        lExpected.append('#                        report is wrong without any warning.')
        lExpected.append('# -max:                  this is the setup check')
        lExpected.append('# maximum output delay:  O_DATA_data maximum - clock minimum + SDIN setup')
        lExpected.append('#                        1.5 - 0.4 + 7')
        lExpected.append('#                        8.1 ns')
        lExpected.append('# objects:               which data port the output delay applies to')
        lExpected.append('#')
        lExpected.append('')
        lExpected.append('set_output_delay -clock [get_clocks clk_capture] -reference_pin [get_ports O_SCLK] -max 8.100 [get_ports O_DATA]')
        lExpected.append('')
        self.assert_lines_in_section('5.1:  O_DATA', lExpected)

    def test_explains_only_the_new_arguments_of_the_minimum_output_delay(self):
        self.run_with_a_deferred_port()
        lExpected = []
        lExpected.append('')
        lExpected.append('#')
        lExpected.append('# -min:                  this is a hold check')
        lExpected.append('# minimum output delay:  O_DATA_data minimum - clock maximum - SDIN hold')
        lExpected.append('#                        0.5 - 1.2 - 2')
        lExpected.append('#                        -2.7 ns')
        lExpected.append('#')
        lExpected.append('')
        lExpected.append('set_output_delay -clock [get_clocks clk_capture] -reference_pin [get_ports O_SCLK] -min -2.700 [get_ports O_DATA]')
        lExpected.append('')
        self.assert_lines_in_section('5.1:  O_DATA', lExpected)

    def test_explains_falling_capture_edges(self):
        self.run_generate_xdc([build_first_last_clock_port_text('O_DATA', 10, 40, [6, 'D'], [8, 'B'])])
        self.assert_lines_in_section('5.1:  O_DATA', ['# -clock_fall:           the capture edges D and B are falling edges of clk_capture'])

    def test_explains_one_falling_capture_edge_used_for_setup_and_hold(self):
        self.run_generate_xdc([build_first_last_clock_port_text('O_DATA', 10, 40, [2, 'B'], [4, 'B'])])
        self.assert_lines_in_section('5.1:  O_DATA', ['# -clock_fall:           the capture edge B is a falling edge of clk_capture'])


class TestGenerateXdcMulticycleComments(XdcFileTestCase):

    def test_explains_each_argument_of_the_setup_multicycle(self):
        self.run_with_a_deferred_port()
        lExpected = []
        lExpected.append('#')
        lExpected.append('# multiplier:  setup requirement / launch period')
        lExpected.append('#              20 ns / 10 ns')
        lExpected.append('#              2')
        lExpected.append('# -setup:      this is the setup multicycle')
        lExpected.append('# -start:      multiplier is relative to the launching clock')
        lExpected.append('# -from:       paths in the design that drive the output port')
        lExpected.append('# -to:         the output data port')
        lExpected.append('#')
        lExpected.append('')
        lExpected.append('set_multicycle_path 2 -setup -start -from [get_clocks clk_launch] -to [get_ports O_DATA]')
        lExpected.append('')
        self.assert_lines_in_section('5.1:  O_DATA', lExpected)

    def test_explains_only_the_new_arguments_of_the_hold_multicycle(self):
        self.run_with_a_deferred_port()
        lExpected = []
        lExpected.append('')
        lExpected.append('#')
        lExpected.append('# multiplier:  (setup requirement - hold requirement) / launch period - 1')
        lExpected.append('#              (20 ns - -20 ns) / 10 ns - 1')
        lExpected.append('#              3')
        lExpected.append('# -hold:       this is the hold multicycle')
        lExpected.append('#')
        lExpected.append('')
        lExpected.append('set_multicycle_path 3 -hold -start -from [get_clocks clk_launch] -to [get_ports O_DATA]')
        self.assertEqual(lExpected, self.read_section('5.1:  O_DATA')[-len(lExpected) - 1:-1])

    def test_counts_capture_periods_when_the_capture_clock_is_faster(self):
        self.run_generate_xdc([build_first_last_clock_port_text('O_DATA', 40, 10, [0, 'E'], [0, 'A'])])
        lExpected = []
        lExpected.append('# multiplier:  setup requirement / capture period')
        lExpected.append('#              20 ns / 10 ns')
        lExpected.append('#              2')
        lExpected.append('# -setup:      this is the setup multicycle')
        lExpected.append('# -end:        multiplier is relative to the capturing clock')
        self.assert_lines_in_section('5.1:  O_DATA', lExpected)

    def test_explains_the_shared_arguments_with_the_hold_multicycle_when_no_setup_multicycle_is_needed(self):
        self.run_generate_xdc([build_first_last_clock_port_text('O_DATA', 10, 40, [6, 'C'], [4, 'A'])])
        lExpected = []
        lExpected.append('#')
        lExpected.append('# multiplier:  (setup requirement - hold requirement) / launch period - 1')
        lExpected.append('#              (10 ns - -20 ns) / 10 ns - 1')
        lExpected.append('#              2')
        lExpected.append('# -hold:       this is the hold multicycle')
        lExpected.append('# -start:      multiplier is relative to the launching clock')
        lExpected.append('# -from:       paths in the design that drive the output port')
        lExpected.append('# -to:         the output data port')
        lExpected.append('#')
        lExpected.append('')
        lExpected.append('set_multicycle_path 2 -hold -start -from [get_clocks clk_launch] -to [get_ports O_DATA]')
        self.assert_lines_in_section('5.1:  O_DATA', lExpected)

    def test_writes_no_multicycle_block_when_the_default_edges_are_timed(self):
        self.run_generate_xdc([build_first_last_clock_port_text('O_DATA', 10, 40, [6, 'C'], [8, 'C'])])
        lSection = self.read_section('5.1:  O_DATA')
        # The last section of the file ends with its last command.
        self.assertEqual('set_output_delay -clock [get_clocks clk_capture] -reference_pin [get_ports O_SCLK] -min -2.700 [get_ports O_DATA]', lSection[-1])


class TestGenerateXdcOutputFile(XdcFileTestCase):

    def run_with_output_option(self):
        self.sOutputFile = os.path.join(self.sDirectory, 'constraints.xdc')
        self.write_file('interface.toml', build_interface_text([build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])], self.sMissingTimingReport))
        oStdout = io.StringIO()
        with mock.patch('sys.argv', ['stacv', 'generate', 'xdc', self.sInterfaceFile, '--output', self.sOutputFile]):
            with contextlib.redirect_stdout(oStdout):
                with self.assertRaises(SystemExit) as oContext:
                    __main__.main()
        return oContext.exception.code, oStdout.getvalue()

    def test_writes_the_constraints_to_the_output_file(self):
        self.run_generate_xdc([build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])])
        sConstraints = self.oStdout.getvalue()
        self.run_with_output_option()
        with open(self.sOutputFile) as oFile:
            self.assertEqual(sConstraints, oFile.read())

    def test_writes_only_the_file_name_to_stdout(self):
        iExitCode, sStdout = self.run_with_output_option()
        self.assertEqual(0, iExitCode)
        self.assertEqual(f'Creating XDC file {self.sOutputFile}\n', sStdout)

