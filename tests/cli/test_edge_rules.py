import contextlib
import io
from unittest import mock

from stacv import __main__
from tests.cli import test_interface_keys

build_interface = test_interface_keys.build_interface

MIXED_CAPTURE_EDGES = 'capture_clock = {name = "clk_capture", setup_edge = "D", hold_edge = "A"}'


class TestEdgeRules(test_interface_keys.InterfaceTestCase):
    '''
    The edge rules are errors that can still be drawn: stacv visualize edges draws the port and reports
    the error in its section, and every other command stops on it.
    '''

    def run_stacv(self, lArguments):
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv'] + lArguments):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def build_mixed_edge_error(self):
        return f'ERROR: [interface_config_018] {self.sInterfaceFile} key "capture_clock" in port O_DATA has setup_edge D and hold_edge A, which are not the same edge type'

    def test_visualize_edges_draws_the_port_and_reports_the_error_in_its_section(self):
        iExitCode = self.run_edges(build_interface({'capture_clock': MIXED_CAPTURE_EDGES}))
        sExpectedEnd = 'hold requirement = -40 ns\n\n' + self.build_mixed_edge_error() + '\n\n'
        self.assertEqual('', self.oStderr.getvalue())
        self.assertIn('Port:  O_DATA', self.oStdout.getvalue())
        self.assertTrue(self.oStdout.getvalue().endswith(sExpectedEnd), self.oStdout.getvalue()[-300:])
        self.assertEqual(2, iExitCode)

    def test_generate_xdc_stops_on_the_error(self):
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(build_interface({'capture_clock': MIXED_CAPTURE_EDGES}))
        iExitCode = self.run_stacv(['generate', 'xdc', self.sInterfaceFile])
        self.assertEqual(self.build_mixed_edge_error() + '\n', self.oStderr.getvalue())
        self.assertEqual('', self.oStdout.getvalue())
        self.assertEqual(2, iExitCode)

    def test_check_stops_on_the_error(self):
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(build_interface({'capture_clock': MIXED_CAPTURE_EDGES}))
        iExitCode = self.run_stacv(['check', self.sInterfaceFile])
        self.assertEqual(self.build_mixed_edge_error() + '\n', self.oStderr.getvalue())
        self.assertEqual(2, iExitCode)

    def test_capture_edges_of_the_same_type_are_drawn_without_an_error(self):
        iExitCode = self.run_edges(build_interface())
        self.assertNotIn('ERROR', self.oStdout.getvalue())
        self.assertEqual(0, iExitCode)


class TestSdrSourceSynchronousOutputEdgeRules(test_interface_keys.InterfaceTestCase):
    '''
    An SDR-SS-O port launches each bit on one edge, and its capture hold edge is the capture edge of the same type before its setup edge.
    '''

    run_stacv = TestEdgeRules.run_stacv

    def build_error(self, sIdentifier, sMessage):
        return f'ERROR: [{sIdentifier}] {self.sInterfaceFile} {sMessage}'

    def assert_error_drawn(self, dReplacements, sError):
        iExitCode = self.run_edges(build_interface(dReplacements))
        self.assertEqual('', self.oStderr.getvalue())
        self.assertIn('Port:  O_DATA', self.oStdout.getvalue())
        self.assertTrue(self.oStdout.getvalue().endswith('\n' + sError + '\n\n'), self.oStdout.getvalue()[-400:])
        self.assertEqual(2, iExitCode)

    def test_launch_setup_and_hold_edges_that_differ_are_an_error(self):
        sLaunchClock = 'launch_clock = {name = "clk_launch", setup_edge = 8, hold_edge = 0}'
        sError = self.build_error('interface_config_019', 'key "launch_clock" in port O_DATA has setup_edge 8 and hold_edge 0; an SDR-SS-O port launches each bit once, so both must be the same edge (a signal timed to the first and last clock edges is SDR-SS-O-FLC)')
        self.assert_error_drawn({'launch_clock': sLaunchClock}, sError)

    def test_capture_hold_edge_that_is_not_the_previous_edge_of_the_same_type_is_an_error(self):
        sCaptureClock = 'capture_clock = {name = "clk_capture", setup_edge = "D", hold_edge = "D"}'
        sError = self.build_error('interface_config_020', 'key "capture_clock" in port O_DATA has setup_edge D and hold_edge D; the hold edge of an SDR-SS-O port is the previous capture edge of the same type, B')
        self.assert_error_drawn({'capture_clock': sCaptureClock}, sError)

    def test_capture_setup_edge_with_no_previous_edge_of_the_same_type_is_an_error(self):
        sCaptureClock = 'capture_clock = {name = "clk_capture", setup_edge = "B", hold_edge = "B"}'
        sError = self.build_error('interface_config_020', 'key "capture_clock" in port O_DATA has setup_edge B and hold_edge B; the hold edge of an SDR-SS-O port is the previous capture edge of the same type, so setup_edge must be C or later')
        self.assert_error_drawn({'capture_clock': sCaptureClock}, sError)

    def test_both_edge_rules_are_reported_in_the_port_section(self):
        sLaunchClock = 'launch_clock = {name = "clk_launch", setup_edge = 8, hold_edge = 0}'
        sCaptureClock = 'capture_clock = {name = "clk_capture", setup_edge = "D", hold_edge = "F"}'
        sLaunchError = self.build_error('interface_config_019', 'key "launch_clock" in port O_DATA has setup_edge 8 and hold_edge 0; an SDR-SS-O port launches each bit once, so both must be the same edge (a signal timed to the first and last clock edges is SDR-SS-O-FLC)')
        sCaptureError = self.build_error('interface_config_020', 'key "capture_clock" in port O_DATA has setup_edge D and hold_edge F; the hold edge of an SDR-SS-O port is the previous capture edge of the same type, B')
        self.assert_error_drawn({'launch_clock': sLaunchClock, 'capture_clock': sCaptureClock}, sLaunchError + '\n' + sCaptureError)

    def test_capture_edges_of_different_types_are_reported_only_as_such(self):
        iExitCode = self.run_edges(build_interface({'capture_clock': MIXED_CAPTURE_EDGES}))
        self.assertIn('interface_config_018', self.oStdout.getvalue())
        self.assertNotIn('interface_config_020', self.oStdout.getvalue())
        self.assertEqual(2, iExitCode)

    def test_check_stops_on_the_launch_edge_rule(self):
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(build_interface({'launch_clock': 'launch_clock = {name = "clk_launch", setup_edge = 8, hold_edge = 0}'}))
        iExitCode = self.run_stacv(['check', self.sInterfaceFile])
        self.assertRegex(self.oStderr.getvalue(), r'^ERROR: \[interface_config_019\] ')
        self.assertEqual(2, iExitCode)

    def test_generate_xdc_stops_on_the_capture_edge_rule(self):
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(build_interface({'capture_clock': 'capture_clock = {name = "clk_capture", setup_edge = "F", hold_edge = "B"}'}))
        iExitCode = self.run_stacv(['generate', 'xdc', self.sInterfaceFile])
        self.assertRegex(self.oStderr.getvalue(), r'^ERROR: \[interface_config_020\] ')
        self.assertEqual('', self.oStdout.getvalue())
        self.assertEqual(2, iExitCode)

    def test_first_last_clock_port_edges_are_independent(self):
        dReplacements = {}
        dReplacements['generator'] = 'idle = "low"\ngenerator = {source = "clock_reg", master_pin = "C", target_pin = "Q", master_clock = "clk_launch"}'
        dReplacements['port'] = '[[port]]\nname = "O_DATA"\nmethodology = "SDR-SS-O-FLC"'
        dReplacements['launch_clock'] = 'launch_clock = {name = "clk_launch", setup_edge = 4, hold_edge = 8}'
        dReplacements['capture_clock'] = 'capture_clock = {name = "clk_capture", setup_edge = "D", hold_edge = "D"}'
        iExitCode = self.run_edges(build_interface(dReplacements))
        self.assertNotIn('ERROR', self.oStdout.getvalue() + self.oStderr.getvalue())
        self.assertEqual(0, iExitCode)


class TestDoubleDataRateInputEdgeRules(test_interface_keys.InterfaceTestCase):
    '''
    A double data rate input names the edge that captures each bit: DDR-SS-I-SE captures on the edge the data is
    aligned with, and DDR-SS-I-NE on the edge after the one it is launched on.
    '''

    run_stacv = TestEdgeRules.run_stacv
    build_error = TestSdrSourceSynchronousOutputEdgeRules.build_error
    assert_error_drawn = TestSdrSourceSynchronousOutputEdgeRules.assert_error_drawn

    def build_replacements(self, sMethodology, iLaunchEdge, sSetupEdge, sHoldEdge):
        dReplacements = {}
        dReplacements['generator'] = None
        dReplacements['port'] = f'[[port]]\nname = "O_DATA"\nmethodology = "{sMethodology}"'
        dReplacements['launch_clock'] = f'launch_clock = {{name = "clk_capture", setup_edge = {iLaunchEdge}, hold_edge = {iLaunchEdge}}}'
        dReplacements['capture_clock'] = f'capture_clock = {{name = "clk_capture", setup_edge = "{sSetupEdge}", hold_edge = "{sHoldEdge}"}}'
        return dReplacements

    def assert_drawn_without_an_error(self, dReplacements):
        iExitCode = self.run_edges(build_interface(dReplacements))
        self.assertNotIn('ERROR', self.oStdout.getvalue() + self.oStderr.getvalue())
        self.assertEqual(0, iExitCode)

    def test_same_edge_capture_is_drawn_without_an_error(self):
        self.assert_drawn_without_an_error(self.build_replacements('DDR-SS-I-SE', 2, 'C', 'B'))

    def test_next_edge_capture_is_drawn_without_an_error(self):
        self.assert_drawn_without_an_error(self.build_replacements('DDR-SS-I-NE', 0, 'B', 'A'))

    def test_same_edge_port_with_next_edge_edges_is_an_error(self):
        sError = self.build_error('interface_config_023', 'the edges in port O_DATA give a setup requirement of 20 ns and a hold requirement of 0 ns; a DDR-SS-I-SE port captures each bit on the edge it is aligned with, so they must be 0 ns and -20 ns')
        self.assert_error_drawn(self.build_replacements('DDR-SS-I-SE', 0, 'B', 'A'), sError)

    def test_next_edge_port_with_same_edge_edges_is_an_error(self):
        sError = self.build_error('interface_config_023', 'the edges in port O_DATA give a setup requirement of 0 ns and a hold requirement of -20 ns; a DDR-SS-I-NE port captures each bit on the edge after the one it is launched on, so they must be 20 ns and 0 ns')
        self.assert_error_drawn(self.build_replacements('DDR-SS-I-NE', 2, 'C', 'B'), sError)

    def test_wrong_hold_edge_alone_is_an_error(self):
        sError = self.build_error('interface_config_023', 'the edges in port O_DATA give a setup requirement of 0 ns and a hold requirement of -40 ns; a DDR-SS-I-SE port captures each bit on the edge it is aligned with, so they must be 0 ns and -20 ns')
        self.assert_error_drawn(self.build_replacements('DDR-SS-I-SE', 2, 'C', 'A'), sError)

    def test_generate_xdc_stops_on_the_rule(self):
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(build_interface(self.build_replacements('DDR-SS-I-SE', 0, 'B', 'A')))
        iExitCode = self.run_stacv(['generate', 'xdc', self.sInterfaceFile])
        self.assertRegex(self.oStderr.getvalue(), r'^ERROR: \[interface_config_023\] ')
        self.assertEqual(2, iExitCode)

    def test_plain_ddr_ss_i_is_not_an_interface_methodology(self):
        # DDR-SS-I is the part's view of the pin; the device names the edge it captures on.
        sMessage = 'key "methodology" in port O_DATA names DDR-SS-I, which stacv does not support; correct it, or defer the port with status = "defer"'
        self.assert_error(self.build_replacements('DDR-SS-I', 2, 'C', 'B'), 'interface_config_011', sMessage)
