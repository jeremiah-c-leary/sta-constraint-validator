import contextlib
import io
from unittest import mock

from stacv import __main__
from tests.cli import test_interface_keys

build_interface = test_interface_keys.build_interface

CAPTURE_CLOCK_WITHOUT_A_PORT = '[[clock]]\nname = "clk_capture"\nperiod = 40.0'


class TestCapturePortAndBuses(test_interface_keys.InterfaceTestCase):

    def run_stacv(self, lArguments, sInterfaceText):
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(sInterfaceText)
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv'] + lArguments + [self.sInterfaceFile]):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def test_capture_clock_without_a_port_stops_generate(self):
        iExitCode = self.run_stacv(['generate', 'xdc'], build_interface({'clock_2': CAPTURE_CLOCK_WITHOUT_A_PORT}))
        sExpected = f'ERROR: [interface_config_021] {self.sInterfaceFile} key "capture_clock" in port O_DATA names clock clk_capture, which has no key "port"; the capture clock leaves the device on a port\n'
        self.assertEqual(sExpected, self.oStderr.getvalue())
        self.assertEqual(2, iExitCode)

    def test_capture_clock_without_a_port_is_still_drawn(self):
        iExitCode = self.run_edges(build_interface({'clock_2': CAPTURE_CLOCK_WITHOUT_A_PORT}))
        self.assertEqual('', self.oStderr.getvalue())
        self.assertEqual(0, iExitCode)

    def test_bus_port_stops_every_command(self):
        sPort = '[[port]]\nname = "O_DATA[7:0]"\nmethodology = "SDR-SS-O"'
        sExpected = f'ERROR: [interface_config_022] {self.sInterfaceFile} port O_DATA[7:0] is a bus, which stacv does not support yet; give each bit its own [[port]], or defer it\n'
        for lCommand in [['visualize', 'edges'], ['generate', 'xdc']]:
            with self.subTest(command=' '.join(lCommand)):
                iExitCode = self.run_stacv(lCommand, build_interface({'port': sPort}))
                self.assertEqual(sExpected, self.oStderr.getvalue())
                self.assertEqual(2, iExitCode)

    def test_port_name_with_a_wildcard_is_a_bus(self):
        sPort = '[[port]]\nname = "O_DATA*"\nmethodology = "SDR-SS-O"'
        iExitCode = self.run_edges(build_interface({'port': sPort}))
        self.assertIn('[interface_config_022]', self.oStderr.getvalue())
        self.assertEqual(2, iExitCode)

    def test_deferred_bus_port_is_ignored(self):
        sDeferredBus = '[[port]]\nstatus = "defer"\nname = "O_DATA[7:0]"\n'
        iExitCode = self.run_edges(build_interface() + sDeferredBus)
        self.assertEqual('', self.oStderr.getvalue())
        self.assertEqual(0, iExitCode)
