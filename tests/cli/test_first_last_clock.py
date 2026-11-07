import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sExampleDir = os.path.join(sProjectDir, 'example', 'texas_instruments', 'DAC81404')

DIVIDER = '=' * 80

LAUNCH_CLOCK_TO_EDGE_8 = [
    '                 0_____1     2_____3     4_____5     6_____7     8',
    'clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|',
    '(100 MHz)',
]

LAUNCH_CLOCK_TO_EDGE_12 = [
    '                                                                             1     1     1',
    '                 0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2',
    'clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|',
    '(100 MHz)',
]


def build_interface_text(sIdle, sMethodology, lLaunchEdges, lCaptureEdges, sTimingReport):
    lText = []
    lText.append('description = "first and last clock test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append('part = "part.toml"')
    lText.append('part_interface = "Serial Interface"')
    lText.append('traces = "traces.toml"')
    lText.append('')
    lText.append('[[clock]]')
    lText.append('name = "clk_100mhz"')
    lText.append('period = 10.000')
    lText.append('')
    lText.append('[[clock]]')
    lText.append('name = "dac_sclk"')
    lText.append('period = 40.000')
    lText.append('port = "O_DAC_SCLK"')
    if sIdle is not None:
        lText.append(f'idle = "{sIdle}"')
    lText.append('generator = {source = "q_spi_output_clock_reg", master_pin = "C", target_pin = "Q", master_clock = "clk_100mhz"}')
    lText.append('')
    lText.append('[[port]]')
    lText.append('name = "O_DAC_DATA"')
    lText.append(f'methodology = "{sMethodology}"')
    lText.append(f'launch_clock = {{name = "clk_100mhz", setup_edge = {lLaunchEdges[0]}, hold_edge = {lLaunchEdges[1]}}}')
    lText.append(f'capture_clock = {{name = "dac_sclk", setup_edge = "{lCaptureEdges[0]}", hold_edge = "{lCaptureEdges[1]}"}}')
    lText.append('registers = ["q_spi_output_data_reg"]')
    lText.append(f'timing_reports = ["{sTimingReport}"]')
    return '\n'.join(lText) + '\n'


class TestFirstLastClock(unittest.TestCase):
    '''
    SDR-SS-O-FLC times a port to the first and last edges of a clock that stops,
    such as a chip select.  The timing is SDR-SS-O; only the edge drawing differs.
    '''

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        self.sInterfaceFile = os.path.join(self.sDirectory, 'interface.toml')

    def write_file(self, sFilename, sText):
        with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
            oFile.write(sText)

    def write_interface(self, sIdle, sMethodology, lLaunchEdges, lCaptureEdges, sTimingReport='O_DAC_DATA_timing.rpt'):
        self.write_file('part.toml', '')
        self.write_file('traces.toml', '')
        self.write_file('interface.toml', build_interface_text(sIdle, sMethodology, lLaunchEdges, lCaptureEdges, sTimingReport))

    def run_stacv(self, lArguments):
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv'] + lArguments):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def build_expected_edges(self, lSetupWindow, sSetupRequirement, lHoldWindow, sHoldRequirement):
        lLines = [DIVIDER, 'Port:  O_DAC_DATA', DIVIDER, '']
        lLines.extend(lSetupWindow)
        lLines.append('')
        lLines.append(sSetupRequirement)
        lLines.append('')
        lLines.extend(lHoldWindow)
        lLines.append('')
        lLines.append(sHoldRequirement)
        lLines.append('')
        return '\n'.join(lLines) + '\n'

    def test_idle_low_clock_draws_a_window_for_the_first_and_the_last_clock(self):
        # The DAC81404 chip select: captured on falling edges, so the clock starts on the rising edge before it.
        self.write_interface('low', 'SDR-SS-O-FLC', [8, 8], ['D', 'B'])
        lSetupWindow = list(LAUNCH_CLOCK_TO_EDGE_12)
        lSetupWindow.append(' ' * 65 + '|---setup requirement-->|')
        lSetupWindow.append(' ' * 47 + 'clock starts ---->|')
        lSetupWindow.append('')
        lSetupWindow.append(' ' * 65 + 'C_______________________D')
        lSetupWindow.append('dac_sclk       ' + '_' * 50 + '|                       |')
        lSetupWindow.append('(25 MHz)')
        lHoldWindow = list(LAUNCH_CLOCK_TO_EDGE_12)
        lHoldWindow.append(' ' * 41 + '|<---hold requirement---|')
        lHoldWindow.append(' ' * 24 + 'clock stops ---->|')
        lHoldWindow.append('')
        lHoldWindow.append(' ' * 17 + 'A_______________________B')
        lHoldWindow.append('dac_sclk       __|                       |' + '_' * 48)
        lHoldWindow.append('(25 MHz)')
        iExitCode = self.run_stacv(['visualize', 'edges', self.sInterfaceFile])
        self.assertEqual('', self.oStderr.getvalue())
        self.assertEqual(0, iExitCode)
        sExpected = self.build_expected_edges(lSetupWindow, 'setup requirement = 20 ns', lHoldWindow, 'hold requirement = -20 ns')
        self.assertEqual(sExpected, self.oStdout.getvalue())

    def test_idle_high_clock_draws_low_pulses(self):
        # Captured on rising edges with the clock idle high: each pulse falls, then rises.
        # The clock stops at A, whose label just fits on its left.
        self.write_interface('high', 'SDR-SS-O-FLC', [4, 4], ['C', 'A'])
        lSetupWindow = list(LAUNCH_CLOCK_TO_EDGE_8)
        lSetupWindow.append(' ' * 41 + '|---setup requirement-->|')
        lSetupWindow.append(' ' * 23 + 'clock starts ---->|')
        lSetupWindow.append('')
        lSetupWindow.append(' ' * 15 + '_' * 26 + 'B' + ' ' * 23 + 'C')
        lSetupWindow.append('dac_sclk' + ' ' * 33 + '|' + '_' * 23 + '|')
        lSetupWindow.append('(25 MHz)')
        lHoldWindow = list(LAUNCH_CLOCK_TO_EDGE_8)
        lHoldWindow.append(' ' * 17 + '|<---hold requirement---|')
        lHoldWindow.append('clock stops ---->|')
        lHoldWindow.append('')
        lHoldWindow.append(' ' * 17 + 'A' + '_' * 48)
        lHoldWindow.append('dac_sclk       __|')
        lHoldWindow.append('(25 MHz)')
        iExitCode = self.run_stacv(['visualize', 'edges', self.sInterfaceFile])
        self.assertEqual('', self.oStderr.getvalue())
        self.assertEqual(0, iExitCode)
        sExpected = self.build_expected_edges(lSetupWindow, 'setup requirement = 20 ns', lHoldWindow, 'hold requirement = -20 ns')
        self.assertEqual(sExpected, self.oStdout.getvalue())

    def test_draws_a_label_on_the_right_when_the_left_has_no_room(self):
        # The clock starts at A, the first edge drawn, which has no room on its left for its label.
        self.write_interface('low', 'SDR-SS-O-FLC', [0, 4], ['B', 'B'])
        lLaunchClock = []
        lLaunchClock.append('                 0_____1     2_____3     4')
        lLaunchClock.append('clk_100mhz     __|     |_____|     |_____|')
        lLaunchClock.append('(100 MHz)')
        lSetupWindow = list(lLaunchClock)
        lSetupWindow.append(' ' * 17 + '|---setup requirement-->|')
        lSetupWindow.append(' ' * 17 + '|<---- clock starts')
        lSetupWindow.append('')
        lSetupWindow.append(' ' * 17 + 'A' + '_' * 23 + 'B')
        lSetupWindow.append('dac_sclk       __|' + ' ' * 23 + '|')
        lSetupWindow.append('(25 MHz)')
        lHoldWindow = list(lLaunchClock)
        lHoldWindow.append(' ' * 41 + '| hold requirement')
        lHoldWindow.append(' ' * 24 + 'clock stops ---->|')
        lHoldWindow.append('')
        lHoldWindow.append(' ' * 17 + 'A' + '_' * 23 + 'B')
        lHoldWindow.append('dac_sclk       __|' + ' ' * 23 + '|')
        lHoldWindow.append('(25 MHz)')
        iExitCode = self.run_stacv(['visualize', 'edges', self.sInterfaceFile])
        self.assertEqual('', self.oStderr.getvalue())
        self.assertEqual(0, iExitCode)
        sExpected = self.build_expected_edges(lSetupWindow, 'setup requirement = 20 ns', lHoldWindow, 'hold requirement = 0 ns')
        self.assertEqual(sExpected, self.oStdout.getvalue())

    def test_sdr_ss_o_port_on_an_idle_clock_is_still_drawn_as_a_continuous_clock(self):
        self.write_interface('low', 'SDR-SS-O', [8, 8], ['D', 'B'])
        iExitCode = self.run_stacv(['visualize', 'edges', self.sInterfaceFile])
        self.assertEqual(0, iExitCode)
        self.assertIn('                                                                 |---setup requirement-->|', self.oStdout.getvalue().split('\n'))
        self.assertIn('                                         |<---hold requirement---|', self.oStdout.getvalue().split('\n'))
        self.assertNotIn('clock starts', self.oStdout.getvalue())

    def test_first_last_clock_port_needs_an_idle_capture_clock(self):
        self.write_interface(None, 'SDR-SS-O-FLC', [8, 8], ['D', 'B'])
        iExitCode = self.run_stacv(['visualize', 'edges', self.sInterfaceFile])
        sExpected = f'ERROR: [interface_config_013] {self.sInterfaceFile} key "capture_clock" in port O_DAC_DATA names clock dac_sclk, which has no key "idle"; SDR-SS-O-FLC is timed to the first and last edges of a clock that stops\n'
        self.assertEqual(2, iExitCode)
        self.assertEqual(sExpected, self.oStderr.getvalue())

    def test_idle_must_be_low_or_high(self):
        self.write_interface('Low', 'SDR-SS-O', [8, 8], ['D', 'B'])
        iExitCode = self.run_stacv(['visualize', 'edges', self.sInterfaceFile])
        sExpected = f'ERROR: [interface_config_012] {self.sInterfaceFile} key "idle" of clock dac_sclk must be "low" or "high"\n'
        self.assertEqual(2, iExitCode)
        self.assertEqual(sExpected, self.oStderr.getvalue())

    def test_first_last_clock_port_runs_the_sdr_ss_o_checks(self):
        # The passing O_DAC_DATA report of the example, checked as SDR-SS-O-FLC.
        sJunitFile = os.path.join(self.sDirectory, 'junit.xml')
        sTimingReport = os.path.join(sProjectDir, 'tests', 'fixtures', 'dac81404', 'timing_reports', 'O_DAC_DATA_timing.rpt')
        lText = build_interface_text('low', 'SDR-SS-O-FLC', [8, 8], ['D', 'B'], sTimingReport).split('\n')
        lText[2] = f'part = "{os.path.join(sProjectDir, "tests", "fixtures", "dac81404", "part.toml")}"'
        lText[4] = f'traces = "{os.path.join(sProjectDir, "tests", "fixtures", "dac81404", "traces.toml")}"'
        # The example part's other pins are not timed here.
        lText.append('[[port]]\nstatus = "defer"\nname = "O_DAC_SDEN_F"\n[[port]]\nstatus = "defer"\nname = "I_DAC_DATA"\n')
        self.write_file('interface.toml', '\n'.join(lText))
        iExitCode = self.run_stacv(['check', self.sInterfaceFile, '--junit', sJunitFile])
        self.assertEqual('', self.oStderr.getvalue())
        self.assertEqual(0, iExitCode)
        self.assertTrue(self.oStdout.getvalue().endswith('Check Passed\n'))
        with open(sJunitFile) as oFile:
            self.assertIn('name="O_DAC_DATA.SDR-SS-O-FLC"', oFile.read())
