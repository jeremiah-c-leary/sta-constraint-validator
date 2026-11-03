import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sExampleDir = 'example/microchip/vsc8540et'
lInterfaces = ['mdio', 'mii', 'rmii', 'rgmii', 'rgmii_id']


class ExampleTestCase(unittest.TestCase):

    def setUp(self):
        sWorkingDir = os.getcwd()
        self.addCleanup(os.chdir, sWorkingDir)
        os.chdir(sProjectDir)
        oEnvironment = mock.patch.dict(os.environ, {'PROJ_DIR': sProjectDir})
        oEnvironment.start()
        self.addCleanup(oEnvironment.stop)

    def run_stacv(self, lArguments):
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv'] + lArguments):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code


class TestVsc8540etExample(ExampleTestCase):
    '''
    Each VSC8540ET interface file generates the constraints and the report script in the example.
    '''

    def test_generated_constraints_match_the_example_constraints_files(self):
        for sInterface in lInterfaces:
            with self.subTest(interface=sInterface):
                iExitCode = self.run_stacv(['generate', 'xdc', f'{sExampleDir}/{sInterface}.toml'])
                with open(f'{sExampleDir}/{sInterface}.xdc') as oFile:
                    sExpected = oFile.read()
                self.assertEqual('', self.oStderr.getvalue())
                self.assertEqual(0, iExitCode)
                self.assertEqual(sExpected, self.oStdout.getvalue())

    def test_generated_report_scripts_match_the_example_report_scripts(self):
        for sInterface in lInterfaces:
            with self.subTest(interface=sInterface):
                sScript = f'{sExampleDir}/{sInterface}_stacv_report.tcl'
                with open(sScript) as oFile:
                    sExpected = oFile.read()
                self.addCleanup(write_file, sScript, sExpected)
                iExitCode = self.run_stacv(['generate', 'report_tcl', f'{sExampleDir}/{sInterface}.toml', '--output', sScript])
                with open(sScript) as oFile:
                    sGenerated = oFile.read()
                self.assertEqual(0, iExitCode)
                self.assertEqual(sExpected, sGenerated)


def write_file(sFilename, sText):
    with open(sFilename, 'w') as oFile:
        oFile.write(sText)


class TestPartInterfaceSelection(unittest.TestCase):
    '''
    The part file's interfaces can share pin names, and the interface file names the one it uses.
    '''

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        with open(os.path.join(sProjectDir, sExampleDir, 'mii.toml')) as oFile:
            self.sInterfaceText = oFile.read()
        with open(os.path.join(sProjectDir, sExampleDir, 'vsc8540et.toml')) as oFile:
            self.sPartText = oFile.read()
        with open(os.path.join(sProjectDir, sExampleDir, 'traces.toml')) as oFile:
            self.sTracesText = oFile.read()
        self.sInterfaceText = self.sInterfaceText.replace('$PROJ_DIR', self.sDirectory)

    def run_generate(self):
        for sName, sText in [('mii.toml', self.sInterfaceText), ('vsc8540et.toml', self.sPartText), ('traces.toml', self.sTracesText)]:
            write_file(os.path.join(self.sDirectory, sName), sText)
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv', 'generate', 'xdc', os.path.join(self.sDirectory, 'mii.toml')]):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def test_part_interface_must_be_an_interface_of_the_part(self):
        self.sInterfaceText = self.sInterfaceText.replace('part_interface = "MII"', 'part_interface = "GMII"')
        self.assertEqual(2, self.run_generate())
        sExpected = f'ERROR: [part_config_009] {os.path.join(self.sDirectory, "vsc8540et.toml")} has no interface named GMII, which key "part_interface" of the interface file names\n'
        self.assertEqual(sExpected, self.oStderr.getvalue())

    def test_pins_are_taken_from_the_named_interface(self):
        # TXD[3:0] is in MII and both RGMII interfaces; MII's setup of 15 ns gives 1.2 + 15 + 1.2.
        self.assertEqual(0, self.run_generate())
        self.assertIn('set_output_delay -clock [get_clocks mii_tx_clk] -max 17.400 [get_ports {O_MII_TXD[*]}]', self.oStdout.getvalue())

    def test_a_pin_gives_one_form_of_its_timing(self):
        self.sPartText = self.sPartText.replace('valid_before = {value = 1.4, symbol = "tSETUP_R", source = "Table 7-27"}', 'cko_max = {value = 1.4, symbol = "tSETUP_R", source = "Table 7-27"}', 1)
        self.assertEqual(2, self.run_generate())
        self.assertIn('[part_config_010]', self.oStderr.getvalue())
        self.assertIn('timing in pin RXD[3:0] of interface Compensated RGMII MAC Interface must give cko_max and cko_min, or valid_before and valid_after', self.oStderr.getvalue())

    def test_a_trace_from_a_source_needs_a_delay(self):
        self.sTracesText = self.sTracesText.replace('part_pin = "RMII_CLKIN"\nsource_to_part = {max_delay = 0.6, min_delay = 0.4}\n', '')
        self.assertEqual(2, self.run_generate())
        self.assertIn('trace rmii_clk_to_part has neither source_to_device nor source_to_part', self.oStderr.getvalue())
