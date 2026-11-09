import contextlib
import io
import os
import re
import tempfile
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


class TestRmiiTemplate(unittest.TestCase):
    '''
    The RMII template, and the tests MII shares, with the values that differ in class attributes.
    '''

    sConfiguration = 'rmii'
    sCreateClock = 'create_clock -name ref_clk_name -period 20.000 [get_ports ref_clk_port]'
    sPlaceholderError = 'ERROR: [rmii_config_006] rmii_config.toml key "name" in [ref_clk] (line 36) is FROM_DESIGN_REF_CLK_NAME; replace it with the name in your design\n'
    sClockPin = 'REF_CLK'
    sDatasheetClockPin = 'RMII_CLKIN'

    def get_config_file(self):
        return f'{self.sConfiguration}_config.toml'

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        sWorkingDir = os.getcwd()
        self.addCleanup(os.chdir, sWorkingDir)

    def run_stacv(self, lArguments):
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv'] + lArguments):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def create_rmii(self):
        return self.run_stacv(['create', 'template', self.sConfiguration, '--output', self.sDirectory])

    def read_file(self, sFilename):
        with open(os.path.join(self.sDirectory, sFilename)) as oFile:
            return oFile.read()

    def write_file(self, sFilename, sText):
        with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
            oFile.write(sText)

    def fill_in(self):
        # The names a user fills in from the design, and the values from the PHY's datasheet.
        sConfig = re.sub(r'"FROM_DESIGN_(\w+)"', lambda oMatch: '"' + oMatch.group(1).lower() + '"', self.read_file(self.get_config_file()))
        self.write_file(self.get_config_file(), sConfig)
        sPart = self.read_file('part.toml')
        sPart = re.sub(r'value = "FROM_DATASHEET\w*"', 'value = 2', sPart)
        sPart = re.sub(r'max_frequency = "FROM_DATASHEET\w*"', 'max_frequency = 50', sPart)
        sPart = re.sub(r'"FROM_DATASHEET\w*"', '"From the datasheet"', sPart)
        self.write_file('part.toml', sPart)

    def test_the_template_is_the_example(self):
        self.assertEqual(0, self.create_rmii())
        for sFilename in [self.get_config_file(), 'part.toml', 'traces.toml']:
            with self.subTest(file=sFilename):
                with open(os.path.join(sProjectDir, 'example', f'{self.sConfiguration}_template', sFilename)) as oFile:
                    self.assertEqual(oFile.read(), self.read_file(sFilename))

    def test_the_filled_in_template_generates_constraints(self):
        self.assertEqual(0, self.create_rmii())
        self.fill_in()
        os.chdir(self.sDirectory)
        self.assertEqual(0, self.run_stacv(['generate', 'xdc', self.get_config_file()]))
        sXdc = self.oStdout.getvalue()
        self.assertIn(self.sCreateClock, sXdc)
        self.assertIn('[get_ports rxd_port]', sXdc)

    def test_a_name_still_to_fill_in_is_an_error(self):
        self.assertEqual(0, self.create_rmii())
        os.chdir(self.sDirectory)
        self.assertEqual(2, self.run_stacv(['generate', 'xdc', self.get_config_file()]))
        self.assertEqual(self.sPlaceholderError, self.oStderr.getvalue())

    def test_the_clock_pin_renamed_to_the_datasheet_name_needs_no_change_to_the_traces(self):
        self.assertEqual(0, self.create_rmii())
        self.fill_in()
        self.write_file('part.toml', self.read_file('part.toml').replace(f'name = "{self.sClockPin}"', f'name = "{self.sDatasheetClockPin}"', 1))
        os.chdir(self.sDirectory)
        self.assertEqual(0, self.run_stacv(['generate', 'xdc', self.get_config_file()]))

    def test_an_spi_option_is_an_error(self):
        self.assertEqual(2, self.run_stacv(['create', 'template', self.sConfiguration, '--mode', '0']))
        self.assertEqual(f'ERROR: [create_002] --mode is an option of the spi template, not of the {self.sConfiguration} template\n', self.oStderr.getvalue())


class TestMiiTemplate(TestRmiiTemplate):

    sConfiguration = 'mii'
    sCreateClock = 'create_clock -name tx_clk_name -period 40.000 [get_ports tx_clk_port]'
    sPlaceholderError = 'ERROR: [mii_config_006] mii_config.toml key "name" in [tx_clk] (line 38) is FROM_DESIGN_TX_CLK_NAME; replace it with the name in your design\n'
    sClockPin = 'TX_CLK'
    sDatasheetClockPin = 'MII_TXCLK'
