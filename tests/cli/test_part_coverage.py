import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# The VSC8540ET's files from before its RMII interface was linked by signal; see the fixture's README.
sExampleDir = os.path.join(sProjectDir, 'tests', 'fixtures', 'vsc8540et')

TX_EN_PORT = '''[[port]]
name = "O_RMII_TX_EN"
methodology = "SDR-SYS-O"
launch_clock = {name = "rmii_ref_clk", setup_edge = 0, hold_edge = 0}
capture_clock = {name = "rmii_ref_clk", setup_edge = 2, hold_edge = 0}
registers = ["q_rmii_tx_en_reg"]
timing_reports = [
    "$PROJ_DIR/example/microchip/vsc8540et/timing_reports/O_RMII_TX_EN_timing.rpt",
]
'''
TX_EN_TRACE = '''[[trace]]
name = "rmii_tx_en"
device_pin = "O_RMII_TX_EN"
part_pin = "TX_EN"
device_to_part = {max_delay = 1.2, min_delay = 0.8}
'''
MDIO_READ_PORT = '''[[port]]
name = "IO_MDIO"
methodology = "SDR-SS-RT-DI"
launch_clock = {name = "mdc", setup_edge = 2, hold_edge = 2}
capture_clock = {name = "clk_100mhz", setup_edge = 156, hold_edge = 76}
registers = ["q_mdio_in_reg"]
timing_reports = [
    "$PROJ_DIR/example/microchip/vsc8540et/timing_reports/IO_MDIO_read_timing.rpt",
]
'''


def read_example_file(sFilename):
    with open(os.path.join(sExampleDir, sFilename)) as oFile:
        return oFile.read()


def replace_once(sText, sOld, sNew):
    if sText.count(sOld) != 1:
        raise ValueError(f'{sOld!r} is not in the text once')
    return sText.replace(sOld, sNew)


class TestPartCoverage(unittest.TestCase):
    '''
    Every pin of the part interface the interface file uses needs a port, analyzed or deferred, through its trace.
    The VSC8540ET example's files are copied, and one is changed.
    '''

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        oEnvironment = mock.patch.dict(os.environ, {'PROJ_DIR': sProjectDir})
        oEnvironment.start()
        self.addCleanup(oEnvironment.stop)
        self.sTracesText = read_example_file('traces.toml')

    def run_stacv(self, sInterface, sInterfaceText, lCommand):
        sInterfaceFile = os.path.join(self.sDirectory, f'{sInterface}.toml')
        for sFilename, sText in [(f'{sInterface}.toml', sInterfaceText), ('vsc8540et.toml', read_example_file('vsc8540et.toml')), ('traces.toml', self.sTracesText)]:
            with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
                oFile.write(sText)
        self.sInterfaceFile = sInterfaceFile
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv'] + lCommand + [sInterfaceFile]):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def run_check_on_rmii(self, sInterfaceText):
        return self.run_stacv('rmii', sInterfaceText, ['check'])

    def build_missing_port_error(self):
        return f'ERROR: [interface_config_024] {self.sInterfaceFile} pin TX_EN (SDR-SYS-I) of part interface RMII has no port; add a [[port]] for it, named O_MII_TX_EN or O_RMII_TX_EN after its trace, or a deferred one\n'

    def test_a_pin_without_a_port_is_an_error(self):
        iExitCode = self.run_check_on_rmii(replace_once(read_example_file('rmii.toml'), TX_EN_PORT, ''))
        self.assertEqual(2, iExitCode)
        self.assertEqual(self.build_missing_port_error(), self.oStderr.getvalue())

    def test_a_deferred_port_covers_its_pin(self):
        sDeferredPort = '[[port]]\nstatus = "defer"\nname = "O_RMII_TX_EN"\n'
        iExitCode = self.run_check_on_rmii(replace_once(read_example_file('rmii.toml'), TX_EN_PORT, sDeferredPort))
        self.assertEqual('', self.oStderr.getvalue())
        self.assertIn('DEFERRED: O_RMII_TX_EN\n', self.oStdout.getvalue())
        self.assertEqual(0, iExitCode)

    def test_a_deferred_port_with_the_methodology_of_another_pin_does_not_cover_it(self):
        # SDR-SS-O times a part pin that is SDR-SS-I; TX_EN is SDR-SYS-I.
        sDeferredPort = '[[port]]\nstatus = "defer"\nname = "O_RMII_TX_EN"\nmethodology = "SDR-SS-O"\n'
        iExitCode = self.run_check_on_rmii(replace_once(read_example_file('rmii.toml'), TX_EN_PORT, sDeferredPort))
        self.assertEqual(2, iExitCode)
        self.assertEqual(self.build_missing_port_error(), self.oStderr.getvalue())

    def test_a_pin_without_a_trace_is_an_error(self):
        # TX_EN of the MII interface has a trace too, so both are removed.
        self.sTracesText = replace_once(self.sTracesText, TX_EN_TRACE, '')
        self.sTracesText = replace_once(self.sTracesText, TX_EN_TRACE.replace('rmii', 'mii').replace('RMII', 'MII'), '')
        iExitCode = self.run_check_on_rmii(read_example_file('rmii.toml'))
        sExpected = f'ERROR: [traces_config_010] {os.path.join(self.sDirectory, "traces.toml")} pin TX_EN (SDR-SYS-I) of part interface RMII has no trace to a device port; add a trace for it, and a [[port]] or a deferred port in the interface file\n'
        self.assertEqual(2, iExitCode)
        self.assertEqual(sExpected, self.oStderr.getvalue())

    def test_each_methodology_of_a_bidirectional_pin_needs_a_port(self):
        iExitCode = self.run_stacv('mdio', replace_once(read_example_file('mdio.toml'), MDIO_READ_PORT, ''), ['check'])
        sExpected = f'ERROR: [interface_config_024] {self.sInterfaceFile} pin MDIO (SDR-SS-RT-DO) of part interface Serial Management Interface has no port; add a [[port]] for it, named IO_MDIO after its trace, or a deferred one\n'
        self.assertEqual(2, iExitCode)
        self.assertEqual(sExpected, self.oStderr.getvalue())

    def test_every_command_that_reads_the_part_stops_on_the_error(self):
        sInterfaceText = replace_once(read_example_file('rmii.toml'), TX_EN_PORT, '')
        for lCommand in [['generate', 'xdc'], ['visualize', 'block_diagram'], ['visualize', 'eye'], ['check']]:
            with self.subTest(command=' '.join(lCommand)):
                iExitCode = self.run_stacv('rmii', sInterfaceText, lCommand)
                self.assertEqual(2, iExitCode)
                self.assertEqual(self.build_missing_port_error(), self.oStderr.getvalue())

    def test_commands_that_read_only_the_interface_file_do_not_check_the_part(self):
        sInterfaceText = replace_once(read_example_file('rmii.toml'), TX_EN_PORT, '')
        for lCommand in [['generate', 'report_tcl'], ['visualize', 'edges']]:
            with self.subTest(command=' '.join(lCommand)):
                self.assertEqual(0, self.run_stacv('rmii', sInterfaceText, lCommand))
                self.assertEqual('', self.oStderr.getvalue())
