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
