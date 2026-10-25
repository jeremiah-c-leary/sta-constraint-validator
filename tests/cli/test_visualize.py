import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__


def build_interface_text(lPorts, sMissingTimingReport):
    lText = []
    lText.append('description = "visualize test"')
    lText.append('interface = "DAC_SPI_1"')
    lText.append('part = "part.toml"')
    lText.append('traces = "traces.toml"')
    for sPort in lPorts:
        lText.append('')
        lText.append(sPort)
        lText.append(f'timing_reports = ["{sMissingTimingReport}"]')
    return '\n'.join(lText) + '\n'


def build_port_text(sName, fLaunchPeriod, fCapturePeriod, lSetupEdges, lHoldEdges):
    lText = []
    lText.append('[[port]]')
    lText.append(f'name = "{sName}"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append(f'launch_clock = {{name = "clk_launch", period = {fLaunchPeriod}, setup_edge = {lSetupEdges[0]}, hold_edge = {lHoldEdges[0]}}}')
    lText.append(f'capture_clock = {{port = "O_CLK", name = "clk_capture", period = {fCapturePeriod}, setup_edge = "{lSetupEdges[1]}", hold_edge = "{lHoldEdges[1]}"}}')
    return '\n'.join(lText)


class VisualizeTestCase(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        self.sInterfaceFile = os.path.join(self.sDirectory, 'interface.toml')
        self.sMissingTimingReport = os.path.join(self.sDirectory, 'not_written_yet.rpt')
        self.write_file('part.toml', '')
        self.write_file('traces.toml', '')

    def write_file(self, sFilename, sText):
        with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
            oFile.write(sText)

    def run_visualize_edges(self, lPorts):
        self.write_file('interface.toml', build_interface_text(lPorts, self.sMissingTimingReport))
        lArgv = ['stacv', 'visualize', 'edges', self.sInterfaceFile]
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', lArgv):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def assert_rows_drawn(self, lExpectedRows):
        self.assertIn('\n' + '\n'.join(lExpectedRows) + '\n', self.oStdout.getvalue())


class TestVisualizeEdgesDispatch(VisualizeTestCase):

    def test_exits_with_zero_when_timing_reports_do_not_exist(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.assertEqual(0, self.run_visualize_edges([sPort]))

    def test_writes_nothing_to_stderr(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.run_visualize_edges([sPort])
        self.assertEqual('', self.oStderr.getvalue())

    def test_exits_with_two_on_interface_error(self):
        self.assertEqual(2, self.run_visualize_edges([]))

    def test_interface_error_is_written_to_stderr(self):
        self.run_visualize_edges([])
        self.assertRegex(self.oStderr.getvalue(), r'^ERROR: \[interface_config_002\] ')


class TestVisualizeEdgesPorts(VisualizeTestCase):

    def test_names_each_port_between_dividers(self):
        lPorts = []
        lPorts.append(build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A']))
        lPorts.append(build_port_text('O_CHIP_SELECT', 10, 40, [4, 'C'], [4, 'A']))
        self.run_visualize_edges(lPorts)
        lLines = self.oStdout.getvalue().split('\n')
        lExpected = []
        lExpected.append('=' * 80)
        lExpected.append('Port:  O_DATA')
        lExpected.append('=' * 80)
        self.assertEqual(lExpected, lLines[0:3])
        iSecondDivider = lLines.index('Port:  O_CHIP_SELECT') - 1
        self.assertEqual('=' * 80, lLines[iSecondDivider])
        self.assertEqual('=' * 80, lLines[iSecondDivider + 2])


class TestVisualizeEdgesClocks(VisualizeTestCase):

    def test_draws_launch_clock_through_one_capture_period_after_the_last_configured_edge(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.run_visualize_edges([sPort])
        lExpected = []
        lExpected.append('                                                                             1     1     1     1     1     1     1')
        lExpected.append('                 0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2_____3     4_____5     6_____')
        lExpected.append('launch clock   __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|')
        self.assert_rows_drawn(lExpected)

    def test_draws_capture_clock_through_one_capture_period_after_the_last_configured_edge(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.run_visualize_edges([sPort])
        lExpected = []
        lExpected.append('                 A_______________________B                       C_______________________D                       E_______________________')
        lExpected.append('capture clock  __|                       |_______________________|                       |_______________________|')
        self.assert_rows_drawn(lExpected)


class TestVisualizeEdgesSetupRequirement(VisualizeTestCase):

    def test_draws_setup_requirement_from_launch_edge_to_capture_edge(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.run_visualize_edges([sPort])
        self.assert_rows_drawn(['                                         |---setup requirement-->|'])

    def test_writes_setup_requirement_after_an_arrow_too_short_to_hold_it(self):
        sPort = build_port_text('O_DATA', 10, 20, [2, 'C'], [2, 'A'])
        self.run_visualize_edges([sPort])
        self.assert_rows_drawn(['                             |---------->| setup requirement'])

    def test_points_setup_requirement_back_at_a_capture_edge_before_the_launch_edge(self):
        sPort = build_port_text('O_DATA', 10, 40, [8, 'A'], [4, 'A'])
        self.run_visualize_edges([sPort])
        self.assert_rows_drawn(['                 |<---------------setup requirement--------------|'])


class TestVisualizeEdgesHoldRequirement(VisualizeTestCase):

    def test_draws_hold_requirement_under_setup_requirement(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.run_visualize_edges([sPort])
        lExpected = []
        lExpected.append('                                         |---setup requirement-->|')
        lExpected.append('                 |<---hold requirement---|')
        self.assert_rows_drawn(lExpected)

    def test_draws_hold_requirement_on_one_column_when_launch_and_capture_edges_line_up(self):
        sPort = build_port_text('O_DATA', 10, 50, [8, 'C'], [0, 'A'])
        self.run_visualize_edges([sPort])
        self.assert_rows_drawn(['                 | hold requirement'])


class TestVisualizeEdgesCombinations(VisualizeTestCase):

    def test_draws_the_whole_example_drawing_for_one_port(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.run_visualize_edges([sPort])
        lExpected = []
        lExpected.append('=' * 80)
        lExpected.append('Port:  O_DATA')
        lExpected.append('=' * 80)
        lExpected.append('')
        lExpected.append('                                                                             1     1     1     1     1     1     1')
        lExpected.append('                 0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2_____3     4_____5     6_____')
        lExpected.append('launch clock   __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|')
        lExpected.append('')
        lExpected.append('                                         |---setup requirement-->|')
        lExpected.append('                 |<---hold requirement---|')
        lExpected.append('')
        lExpected.append('                 A_______________________B                       C_______________________D                       E_______________________')
        lExpected.append('capture clock  __|                       |_______________________|                       |_______________________|')
        lExpected.append('')
        self.assertEqual('\n'.join(lExpected) + '\n', self.oStdout.getvalue())

    def test_draws_a_capture_period_five_times_the_launch_period(self):
        sPort = build_port_text('O_DATA', 10, 50, [8, 'C'], [0, 'A'])
        self.run_visualize_edges([sPort])
        lExpected = []
        lExpected.append('                                                                             1     1     1     1     1     1     1     1     1     1     2')
        lExpected.append('                 0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2_____3     4_____5     6_____7     8_____9     0_____')
        lExpected.append('launch clock   __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|')
        lExpected.append('')
        lExpected.append('                                                                 |---------->| setup requirement')
        lExpected.append('                 | hold requirement')
        lExpected.append('')
        lExpected.append('                 A_____________________________B                             C_____________________________D                             E_____________________________')
        lExpected.append('capture clock  __|                             |_____________________________|                             |_____________________________|')
        self.assert_rows_drawn(lExpected)

    def test_gives_the_shortest_half_period_six_columns_when_the_capture_clock_is_faster(self):
        sPort = build_port_text('O_DATA', 40, 10, [2, 'K'], [2, 'I'])
        self.run_visualize_edges([sPort])
        lExpected = []
        lExpected.append('                 0_______________________1                       2_______________________3')
        lExpected.append('launch clock   __|                       |_______________________|                       |_______________________')
        lExpected.append('')
        lExpected.append('                                                                 |---------->| setup requirement')
        lExpected.append('                                                                 | hold requirement')
        lExpected.append('')
        lExpected.append('                 A_____B     C_____D     E_____F     G_____H     I_____J     K_____L     M_____')
        lExpected.append('capture clock  __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|')
        self.assert_rows_drawn(lExpected)

    def test_rounds_an_edge_between_columns_half_up(self):
        sPort = build_port_text('O_DATA', 10, 12.5, [2, 'C'], [2, 'A'])
        self.run_visualize_edges([sPort])
        lExpected = []
        lExpected.append('                 0_____1     2_____3     4_____5')
        lExpected.append('launch clock   __|     |_____|     |_____|     |_____')
        lExpected.append('')
        lExpected.append('                             |->| setup requirement')
        lExpected.append('                 |<----------| hold requirement')
        lExpected.append('')
        lExpected.append('                 A_______B      C_______D      E_______')
        lExpected.append('capture clock  __|       |______|       |______|')
        self.assert_rows_drawn(lExpected)

    def test_draws_tens_digits_above_edge_numbers_past_nineteen(self):
        sPort = build_port_text('O_DATA', 10, 100, [10, 'C'], [10, 'A'])
        self.run_visualize_edges([sPort])
        lExpected = []
        lExpected.append('                                                                             1     1     1     1     1     1     1     1     1     1     2     2     2     2     2     2     2     2     2     2     3     3     3     3     3     3     3     3     3     3     4')
        lExpected.append('                 0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2_____3     4_____5     6_____7     8_____9     0_____')
        lExpected.append('launch clock   __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|')
        lExpected.append('')
        lExpected.append('                                                                             |---------------------setup requirement-------------------->|')
        lExpected.append('                 |<---------------------hold requirement---------------------|')
        lExpected.append('')
        lExpected.append('                 A___________________________________________________________B                                                           C___________________________________________________________D                                                           E___________________________________________________________')
        lExpected.append('capture clock  __|                                                           |___________________________________________________________|                                                           |___________________________________________________________|')
        self.assert_rows_drawn(lExpected)
