import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__

ROUND_TRIP = 'SDR-SS-RT-DI'
GENERATOR = '{source = "q_sclk_reg", master_pin = "C", target_pin = "Q", master_clock = "clk_sys"}'
OTHER_GENERATOR = '{source = "q_other_reg", master_pin = "C", target_pin = "Q", master_clock = "clk_sys"}'
BANNER = '#' * 79

# An SDR-SS-RT-DI port forwards its launch clock, clk_sclk, to the part on O_SCLK.
# The part launches SDO on that clock, and the device captures it on I_DATA with clk_sys.
# With clk_sclk at 80 ns and clk_sys at 10 ns:
#    launch edge 2   is at (80 / 2) * 2  = 80 ns
#    capture edge Y  is at (10 / 2) * 24 = 120 ns, a setup requirement of 40 ns
#    capture edge I  is at (10 / 2) * 8  = 40 ns, a hold requirement of -40 ns
# The input delays are:
#    maximum:  clock maximum + SDO cko_max + data_input maximum = 1.2 + 30 + 1.5 = 32.7 ns
#    minimum:  clock minimum + SDO cko_min + data_input minimum = 0.4 + 0 + 0.5  = 0.9 ns
PASSING_SETUP_EDGES = [2, 'Y']
PASSING_HOLD_EDGES = [2, 'I']


def build_system_clock_table():
    lText = []
    lText.append('[[clock]]')
    lText.append('name = "clk_sys"')
    lText.append('period = 10')
    return '\n'.join(lText)


def build_forwarded_clock_table(sName, fPeriod, sGenerator=GENERATOR, sPort='O_SCLK'):
    lText = []
    lText.append('[[clock]]')
    lText.append(f'name = "{sName}"')
    lText.append(f'period = {fPeriod}')
    if sPort is not None:
        lText.append(f'port = "{sPort}"')
    if sGenerator is not None:
        lText.append(f'generator = {sGenerator}')
    return '\n'.join(lText)


def build_round_trip_port_table(sName, sLaunchClock, lSetupEdges, lHoldEdges, sTimingReport):
    lText = []
    lText.append('[[port]]')
    lText.append(f'name = "{sName}"')
    lText.append(f'methodology = "{ROUND_TRIP}"')
    lText.append(f'launch_clock = {{name = "{sLaunchClock}", setup_edge = {lSetupEdges[0]}, hold_edge = {lHoldEdges[0]}}}')
    lText.append(f'capture_clock = {{name = "clk_sys", setup_edge = "{lSetupEdges[1]}", hold_edge = "{lHoldEdges[1]}"}}')
    lText.append(f'timing_reports = ["{sTimingReport}"]')
    return '\n'.join(lText)


def build_output_port_table(sName, sCaptureClock, sTimingReport):
    lText = []
    lText.append('[[port]]')
    lText.append(f'name = "{sName}"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append('launch_clock = {name = "clk_sys", setup_edge = 8, hold_edge = 8}')
    lText.append(f'capture_clock = {{name = "{sCaptureClock}", setup_edge = "D", hold_edge = "B"}}')
    lText.append(f'timing_reports = ["{sTimingReport}"]')
    return '\n'.join(lText)


def build_interface_text(lTables):
    lText = []
    lText.append('description = "round trip test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append('part = "part.toml"')
    lText.append('part_interface = "Serial Interface"')
    lText.append('traces = "traces.toml"')
    for sTable in lTables:
        lText.append('')
        lText.append(sTable)
    return '\n'.join(lText) + '\n'


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
    lText.append('setup = {value = 10, symbol = "tSDIS", source = "Table 7.6"}')
    lText.append('hold = {value = 10, symbol = "tSDIH", source = "Table 7.6"}')
    lText.append('')
    lText.append('[[interface.pin]]')
    lText.append('name = "SDO"')
    lText.append('methodology = "SDR-SS-RT-DO"')
    lText.append('clock = {pin = "SCLK", max_frequency = 12.5}')
    lText.append('cko_max = {value = 30, symbol = "tSDODLY", source = "Table 7.8"}')
    lText.append('cko_min = {value = 0, symbol = "tSDODLY", source = "Table 7.8"}')
    lText.append('launch_edge = "Rising"')
    return '\n'.join(lText) + '\n'


def build_traces_text(bWithDataInput=True):
    lText = []
    if bWithDataInput:
        lText.append('[[trace]]')
        lText.append('name = "data_input"')
        lText.append('device_pin = "I_DATA"')
        lText.append('part_pin = "SDO"')
        lText.append('part_to_device = {max_delay = 1.5, min_delay = 0.5}')
        lText.append('')
    lText.append('[[trace]]')
    lText.append('name = "data_output"')
    lText.append('device_pin = "O_DATA"')
    lText.append('part_pin = "SDIN"')
    lText.append('device_to_part = {max_delay = 3.0, min_delay = 1.0}')
    lText.append('')
    lText.append('[[trace]]')
    lText.append('name = "clock"')
    lText.append('device_pin = "O_SCLK"')
    lText.append('part_pin = "SCLK"')
    lText.append('device_to_part = {max_delay = 1.2, min_delay = 0.4}')
    return '\n'.join(lText) + '\n'


class RoundTripTestCase(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        self.sInterfaceFile = os.path.join(self.sDirectory, 'interface.toml')
        self.sMissingTimingReport = os.path.join(self.sDirectory, 'not_written_yet.rpt')
        self.write_file('part.toml', build_part_text())
        self.write_file('traces.toml', build_traces_text())

    def write_file(self, sFilename, sText):
        with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
            oFile.write(sText)

    def build_round_trip_tables(self, lSetupEdges=PASSING_SETUP_EDGES, lHoldEdges=PASSING_HOLD_EDGES, sGenerator=GENERATOR, sPort='O_SCLK'):
        lTables = []
        lTables.append(build_system_clock_table())
        lTables.append(build_forwarded_clock_table('clk_sclk', 80, sGenerator, sPort))
        lTables.append(build_round_trip_port_table('I_DATA', 'clk_sclk', lSetupEdges, lHoldEdges, self.sMissingTimingReport))
        return lTables

    def run_stacv(self, lTables, lArguments):
        self.write_file('interface.toml', build_interface_text(lTables))
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv'] + lArguments):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def run_generate_xdc(self, lTables):
        return self.run_stacv(lTables, ['generate', 'xdc', self.sInterfaceFile])

    def get_output_lines(self):
        return self.oStdout.getvalue().split('\n')

    def assert_line_written(self, sExpectedLine):
        self.assertIn(sExpectedLine, self.get_output_lines())

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

    def read_port_constraints(self, sTitle):
        # The constraints follow the line that ends the edges and requirements.
        lSection = self.read_section(sTitle)
        return lSection[lSection.index('#' + '-' * 78) + 1:]


class TestRoundTripGeneratedClock(RoundTripTestCase):

    def test_generates_the_launch_clock_of_a_round_trip_port(self):
        self.assertEqual(0, self.run_generate_xdc(self.build_round_trip_tables()))
        lSection = self.read_section('4.1:  clk_sclk Generated Clock')
        self.assertIn('create_generated_clock -name clk_sclk -source [get_pins q_sclk_reg/C] -divide_by 8 [get_pins q_sclk_reg/Q]', lSection)

    def test_reports_a_launch_clock_without_a_generator(self):
        self.assertEqual(2, self.run_generate_xdc(self.build_round_trip_tables(sGenerator=None)))
        self.assertEqual('ERROR: [generate_001] port I_DATA launch clock clk_sclk has no generator\n', self.oStderr.getvalue())

    def test_reports_a_launch_clock_without_a_port(self):
        self.assertEqual(2, self.run_generate_xdc(self.build_round_trip_tables(sPort=None)))
        sExpected = f'ERROR: [interface_config_021] {self.sInterfaceFile} key "launch_clock" in port I_DATA names clock clk_sclk, which has no key "port"; the launch clock leaves the device on a port\n'
        self.assertEqual(sExpected, self.oStderr.getvalue())

    def build_write_and_read_tables(self, sReadGenerator):
        # The device writes with clk_sclk_wr and reads with clk_sclk_rd, both forwarded on O_SCLK.
        lTables = []
        lTables.append(build_system_clock_table())
        lTables.append(build_forwarded_clock_table('clk_sclk_wr', 40))
        lTables.append(build_forwarded_clock_table('clk_sclk_rd', 80, sReadGenerator))
        lTables.append(build_output_port_table('O_DATA', 'clk_sclk_wr', self.sMissingTimingReport))
        lTables.append(build_round_trip_port_table('I_DATA', 'clk_sclk_rd', PASSING_SETUP_EDGES, PASSING_HOLD_EDGES, self.sMissingTimingReport))
        return lTables

    def test_adds_a_second_clock_generated_at_the_same_pin(self):
        self.assertEqual(0, self.run_generate_xdc(self.build_write_and_read_tables(GENERATOR)))
        lExpected = []
        lExpected.append('#')
        lExpected.append('# -add:           allows for more than one clock to be generated from the same target')
        lExpected.append('# -master_clock:  the name of the source clock')
        lExpected.append('# -name:          the name of the generated clock')
        lExpected.append('# -source:        clk_sclk_rd is generated by q_sclk_reg, from clk_sys at pin C to pin Q')
        lExpected.append('# -divide_by:     clk_sclk_rd period / clk_sys period')
        lExpected.append('#                 80 ns / 10 ns')
        lExpected.append('#                 8')
        lExpected.append('# objects:        where the generated clock starts')
        lExpected.append('#')
        lExpected.append('')
        lExpected.append('create_generated_clock -add -master_clock [get_clocks clk_sys] -name clk_sclk_rd -source [get_pins q_sclk_reg/C] -divide_by 8 [get_pins q_sclk_reg/Q]')
        lExpected.append('')
        self.assertEqual(lExpected, self.read_section('4.2:  clk_sclk_rd Generated Clock'))

    def test_does_not_add_the_first_clock_generated_at_a_pin(self):
        self.run_generate_xdc(self.build_write_and_read_tables(GENERATOR))
        self.assert_line_written('create_generated_clock -name clk_sclk_wr -source [get_pins q_sclk_reg/C] -divide_by 4 [get_pins q_sclk_reg/Q]')

    def test_does_not_add_a_clock_generated_at_another_pin(self):
        self.run_generate_xdc(self.build_write_and_read_tables(OTHER_GENERATOR))
        self.assert_line_written('create_generated_clock -name clk_sclk_rd -source [get_pins q_other_reg/C] -divide_by 8 [get_pins q_other_reg/Q]')


class TestRoundTripConstraints(RoundTripTestCase):

    def test_explains_each_input_delay_and_multicycle(self):
        self.assertEqual(0, self.run_generate_xdc(self.build_round_trip_tables()))
        lExpected = []
        lExpected.append('#')
        lExpected.append('# -clock:               the launch clock')
        lExpected.append('# -reference_pin:       clk_sclk is generated at q_sclk_reg/Q.  Without the reference pin,')
        lExpected.append('#                       the delay from Q to O_SCLK is left out of the clock path and the timing')
        lExpected.append('#                       report is wrong without any warning.')
        lExpected.append('# -max:                 this is the setup check')
        lExpected.append('# maximum input delay:  clock maximum + part clock to out maximum + data_input maximum')
        lExpected.append('#                       1.2 + 30 + 1.5')
        lExpected.append('#                       32.7 ns')
        lExpected.append('# objects:              which data port the input delay applies to')
        lExpected.append('#')
        lExpected.append('')
        lExpected.append('set_input_delay -clock [get_clocks clk_sclk] -reference_pin [get_ports O_SCLK] -max 32.700 [get_ports I_DATA]')
        lExpected.append('')
        lExpected.append('#')
        lExpected.append('# -min:                 this is a hold check')
        lExpected.append('# minimum input delay:  clock minimum + part clock to out minimum + data_input minimum')
        lExpected.append('#                       0.4 + 0 + 0.5')
        lExpected.append('#                       0.9 ns')
        lExpected.append('#')
        lExpected.append('')
        lExpected.append('set_input_delay -clock [get_clocks clk_sclk] -reference_pin [get_ports O_SCLK] -min 0.900 [get_ports I_DATA]')
        lExpected.append('')
        lExpected.append('#')
        lExpected.append('# multiplier:  setup requirement / capture period')
        lExpected.append('#              40 ns / 10 ns')
        lExpected.append('#              4')
        lExpected.append('# -setup:      this is the setup multicycle')
        lExpected.append('# -end:        multiplier is relative to the capturing clock')
        lExpected.append('# -from:       the port on the device that receives data from the part')
        lExpected.append('# -to:         the clock in the device that captures data')
        lExpected.append('#')
        lExpected.append('')
        lExpected.append('set_multicycle_path 4 -setup -end -from [get_ports I_DATA] -to [get_clocks clk_sys]')
        lExpected.append('')
        lExpected.append('#')
        lExpected.append('# multiplier:  (setup requirement - hold requirement) / capture period - 1')
        lExpected.append('#              (40 ns - -40 ns) / 10 ns - 1')
        lExpected.append('#              7')
        lExpected.append('# -hold:       this is the hold multicycle')
        lExpected.append('#')
        lExpected.append('')
        lExpected.append('set_multicycle_path 7 -hold -end -from [get_ports I_DATA] -to [get_clocks clk_sys]')
        self.assertEqual(lExpected, self.read_port_constraints('5.1:  I_DATA'))

    def test_starts_with_the_requirements_and_their_edges(self):
        self.run_generate_xdc(self.build_round_trip_tables())
        lSection = self.read_section('5.1:  I_DATA')
        self.assertIn('# setup requirement:  40 ns (launch edge 2 at 80 ns -> capture edge Y at 120 ns)', lSection)
        self.assertIn('# hold requirement:  -40 ns (launch edge 2 at 80 ns -> capture edge I at 40 ns)', lSection)

    def test_applies_the_input_delays_to_a_falling_launch_edge(self):
        # Launch edge 1 is at 40 ns, capture edge Q at 80 ns and capture edge A at 0 ns.
        self.assertEqual(0, self.run_generate_xdc(self.build_round_trip_tables([1, 'Q'], [1, 'A'])))
        self.assert_line_written('set_input_delay -clock [get_clocks clk_sclk] -clock_fall -reference_pin [get_ports O_SCLK] -max 32.700 [get_ports I_DATA]')
        self.assert_line_written('set_input_delay -clock [get_clocks clk_sclk] -clock_fall -reference_pin [get_ports O_SCLK] -min 0.900 [get_ports I_DATA]')
        self.assertIn('# -clock_fall:          the launch edge 1 is a falling edge of clk_sclk', self.read_section('5.1:  I_DATA'))

    def test_reports_a_port_without_a_trace_from_the_part(self):
        self.write_file('traces.toml', build_traces_text(bWithDataInput=False))
        self.assertEqual(2, self.run_generate_xdc(self.build_round_trip_tables()))
        self.assertEqual('ERROR: [generate_007] port I_DATA has no trace from the part to the device\n', self.oStderr.getvalue())


class TestRoundTripEdges(RoundTripTestCase):

    def test_draws_the_edges_to_the_launch_clock_edge_after_the_last_edge(self):
        # The last edge is capture edge Y at 120 ns, and the next edge of the forwarded clock is launch edge 4 at 160 ns.
        self.assertEqual(0, self.run_stacv(self.build_round_trip_tables(), ['visualize', 'edges', self.sInterfaceFile]))
        lLines = self.get_output_lines()
        sHigh = '_' * 47
        sLow = ' ' * 47
        iLaunchLabels = lLines.index('                 0' + sHigh + '1' + sLow + '2' + sHigh + '3' + sLow + '4')
        self.assertEqual('clk_sclk       __|' + sLow + '|' + sHigh + '|' + sLow + '|' + sHigh + '|', lLines[iLaunchLabels + 1])
        # Capture edge AG, at 160 ns, has its first letter in the row above.
        self.assertTrue(lLines[iLaunchLabels + 6].endswith('A'))
        self.assertTrue(lLines[iLaunchLabels + 7].endswith('G'))
        self.assertTrue(lLines[iLaunchLabels + 8].startswith('clk_sys        __|'))


class TestRoundTripReportScript(RoundTripTestCase):

    def test_reports_the_paths_from_the_input_port(self):
        self.assertEqual(0, self.run_stacv(self.build_round_trip_tables(), ['generate', 'report_tcl', self.sInterfaceFile]))
        sOptions = f'-max_paths 100 -nworst 100 -path full_clock_expanded -append -file "{self.sMissingTimingReport}"'
        self.assert_line_written(f'report_timing -column_style variable_width -from [get_clocks clk_sclk] -through [get_ports I_DATA] -setup -max_paths 100 -nworst 100 -path full_clock_expanded -file "{self.sMissingTimingReport}"')
        self.assert_line_written(f'report_timing -column_style variable_width -from [get_clocks clk_sclk] -through [get_ports I_DATA] -hold {sOptions}')
        self.assert_line_written(f'report_timing -column_style variable_width -from [get_clocks clk_sclk] -through [get_ports I_DATA] -setup {sOptions}')


class TestRoundTripCheck(RoundTripTestCase):

    def test_reads_the_timing_reports_of_a_round_trip_port(self):
        # The SDR-SS-RT-DI rules read the timing reports, so a report that is not written yet is an input error.
        iExitCode = self.run_stacv(self.build_round_trip_tables(), ['check', self.sInterfaceFile])
        self.assertEqual(2, iExitCode)
        self.assertIn('[interface_config_006]', self.oStderr.getvalue())
