import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__

CLOCK_KEYS = 'name, period, port, idle, generator'
PORT_KEYS = 'status, name, methodology, launch_clock, capture_clock, registers, timing_reports'


def build_interface(dReplacements=None):
    # Each replacement maps a line's key to its new line, or to None to remove the line.
    dLines = {}
    dLines['description'] = 'description = "interface keys test"'
    dLines['name'] = 'name = "DAC_SPI_1"'
    dLines['part'] = 'part = "part.toml"'
    dLines['part_interface'] = 'part_interface = "Serial Interface"'
    dLines['traces'] = 'traces = "traces.toml"'
    dLines['clock_1'] = '[[clock]]\nname = "clk_launch"\nperiod = 10.0'
    dLines['clock_2'] = '[[clock]]\nname = "clk_capture"\nperiod = 40.0\nport = "O_CLK"'
    dLines['generator'] = 'generator = {source = "clock_reg", master_pin = "C", target_pin = "Q", master_clock = "clk_launch"}'
    dLines['port'] = '[[port]]\nname = "O_DATA"\nmethodology = "SDR-SS-O"'
    dLines['launch_clock'] = 'launch_clock = {name = "clk_launch", setup_edge = 8, hold_edge = 8}'
    dLines['capture_clock'] = 'capture_clock = {name = "clk_capture", setup_edge = "D", hold_edge = "B"}'
    dLines['timing_reports'] = 'timing_reports = ["O_DATA_timing.rpt"]'
    if dReplacements is not None:
        dLines.update(dReplacements)
    lText = []
    for sLine in dLines.values():
        if sLine is not None:
            lText.append(sLine)
    return '\n'.join(lText) + '\n'


class InterfaceTestCase(unittest.TestCase):
    '''
    Runs stacv visualize edges on an interface file, with empty part and traces files beside it.
    '''

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        self.sInterfaceFile = os.path.join(self.sDirectory, 'interface.toml')
        for sFilename in ['part.toml', 'traces.toml']:
            with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
                oFile.write('')

    def run_edges(self, sInterfaceText):
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(sInterfaceText)
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv', 'visualize', 'edges', self.sInterfaceFile]):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def assert_error(self, dReplacements, sIdentifier, sMessage):
        iExitCode = self.run_edges(build_interface(dReplacements))
        self.assertEqual(f'ERROR: [{sIdentifier}] {self.sInterfaceFile} {sMessage}\n', self.oStderr.getvalue())
        self.assertEqual(2, iExitCode)


class TestInterfaceKeys(InterfaceTestCase):
    '''
    Every key of every interface table is checked: unknown keys, missing keys and the type of each value.
    '''

    def test_valid_interface_draws_its_edges(self):
        iExitCode = self.run_edges(build_interface())
        self.assertEqual('', self.oStderr.getvalue())
        self.assertEqual(0, iExitCode)

    def test_unknown_top_level_key_is_an_error(self):
        self.assert_error({'traces': 'tracess = "traces.toml"\ntraces = "traces.toml"'}, 'interface_config_004', 'key "tracess" is not a key stacv reads; the keys are description, name, part, part_interface, traces, clock, port')

    def test_unknown_clock_key_is_an_error(self):
        self.assert_error({'generator': 'idel = "low"'}, 'interface_config_004', f'key "idel" of clock clk_capture is not a key stacv reads; the keys are {CLOCK_KEYS}')

    def test_unknown_generator_key_is_an_error(self):
        sGenerator = 'generator = {source = "clock_reg", master_pn = "C", target_pin = "Q", master_clock = "clk_launch"}'
        self.assert_error({'generator': sGenerator}, 'interface_config_004', 'key "master_pn" in generator of clock clk_capture is not a key stacv reads; the keys are source, master_pin, target_pin, master_clock')

    def test_misspelled_status_is_an_unknown_key(self):
        self.assert_error({'port': '[[port]]\nstauts = "defer"\nname = "O_DATA"\nmethodology = "SDR-SS-O"'}, 'interface_config_004', f'key "stauts" in port O_DATA is not a key stacv reads; the keys are {PORT_KEYS}')

    def test_unknown_key_in_capture_clock_is_an_error(self):
        sCaptureClock = 'capture_clock = {name = "clk_capture", setup_egde = "D", hold_edge = "B"}'
        self.assert_error({'capture_clock': sCaptureClock}, 'interface_config_004', 'key "setup_egde" in capture_clock of port O_DATA is not a key stacv reads; the keys are name, setup_edge, hold_edge')

    def test_deferred_port_keys_are_not_checked(self):
        sPort = '[[port]]\nstatus = "defer"\nname = "O_CS"\nchip_select = true'
        iExitCode = self.run_edges(build_interface()+ sPort + '\n')
        self.assertEqual('', self.oStderr.getvalue())
        self.assertEqual(0, iExitCode)

    def test_clock_without_a_period_is_an_error(self):
        self.assert_error({'clock_1': '[[clock]]\nname = "clk_launch"'}, 'interface_config_002', 'missing required key "period" of clock clk_launch')

    def test_clock_without_a_name_is_named_by_its_number(self):
        self.assert_error({'clock_2': '[[clock]]\nperiod = 40.0\nport = "O_CLK"'}, 'interface_config_002', 'missing required key "name" of clock number 2')

    def test_generator_without_a_master_pin_is_an_error(self):
        sGenerator = 'generator = {source = "clock_reg", target_pin = "Q", master_clock = "clk_launch"}'
        self.assert_error({'generator': sGenerator}, 'interface_config_002', 'missing required key "master_pin" in generator of clock clk_capture')

    def test_capture_clock_without_a_hold_edge_is_an_error(self):
        self.assert_error({'capture_clock': 'capture_clock = {name = "clk_capture", setup_edge = "D"}'}, 'interface_config_002', 'missing required key "hold_edge" in capture_clock of port O_DATA')

    def test_period_must_be_a_number(self):
        self.assert_error({'clock_1': '[[clock]]\nname = "clk_launch"\nperiod = "10.0"'}, 'interface_config_003', 'key "period" of clock clk_launch must be a number')

    def test_generator_must_be_a_table(self):
        self.assert_error({'generator': 'generator = "clock_reg"'}, 'interface_config_003', 'key "generator" of clock clk_capture must be a table')

    def test_launch_clock_must_be_a_table(self):
        self.assert_error({'launch_clock': 'launch_clock = "clk_launch"'}, 'interface_config_003', 'key "launch_clock" in port O_DATA must be a table')
