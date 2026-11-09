import contextlib
import io
import os
import re
import tempfile
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sExampleDir = os.path.join(sProjectDir, 'example', 'rmii_template')
FILE_NAMES = ['rmii_config.toml', 'part.toml', 'traces.toml']


class TestRmiiTemplate(unittest.TestCase):

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
        return self.run_stacv(['create', 'template', 'rmii', '--output', self.sDirectory])

    def read_file(self, sFilename):
        with open(os.path.join(self.sDirectory, sFilename)) as oFile:
            return oFile.read()

    def write_file(self, sFilename, sText):
        with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
            oFile.write(sText)

    def fill_in(self):
        # The names a user fills in from the design, and the values from the PHY's datasheet.
        sConfig = re.sub(r'"FROM_DESIGN_(\w+)"', lambda oMatch: '"' + oMatch.group(1).lower() + '"', self.read_file('rmii_config.toml'))
        self.write_file('rmii_config.toml', sConfig)
        sTraces = self.read_file('traces.toml').replace('"FROM_DESIGN_REF_CLK_PORT"', '"ref_clk_port"')
        self.write_file('traces.toml', sTraces)
        sPart = self.read_file('part.toml')
        sPart = re.sub(r'value = "FROM_DATASHEET\w*"', 'value = 2', sPart)
        sPart = re.sub(r'max_frequency = "FROM_DATASHEET\w*"', 'max_frequency = 50', sPart)
        sPart = re.sub(r'"FROM_DATASHEET\w*"', '"From the datasheet"', sPart)
        self.write_file('part.toml', sPart)

    def test_the_template_is_the_example(self):
        self.assertEqual(0, self.create_rmii())
        for sFilename in FILE_NAMES:
            with self.subTest(file=sFilename):
                with open(os.path.join(sExampleDir, sFilename)) as oFile:
                    self.assertEqual(oFile.read(), self.read_file(sFilename))

    def test_the_filled_in_template_generates_constraints(self):
        self.assertEqual(0, self.create_rmii())
        self.fill_in()
        os.chdir(self.sDirectory)
        self.assertEqual(0, self.run_stacv(['generate', 'xdc', 'rmii_config.toml']))
        sXdc = self.oStdout.getvalue()
        self.assertIn('create_clock -name ref_clk_name -period 20.000 [get_ports ref_clk_port]', sXdc)
        self.assertIn('[get_ports rxd_port]', sXdc)

    def test_a_name_still_to_fill_in_is_an_error(self):
        self.assertEqual(0, self.create_rmii())
        os.chdir(self.sDirectory)
        self.assertEqual(2, self.run_stacv(['generate', 'xdc', 'rmii_config.toml']))
        self.assertEqual('ERROR: [rmii_config_006] rmii_config.toml key "name" in [ref_clk] (line 34) is FROM_DESIGN_REF_CLK_NAME; replace it with the name in your design\n', self.oStderr.getvalue())

    def test_a_reference_clock_port_still_to_fill_in_in_the_traces_is_an_error(self):
        self.assertEqual(0, self.create_rmii())
        self.fill_in()
        self.write_file('traces.toml', self.read_file('traces.toml').replace('"ref_clk_port"', '"FROM_DESIGN_REF_CLK_PORT"'))
        os.chdir(self.sDirectory)
        self.assertEqual(2, self.run_stacv(['generate', 'xdc', 'rmii_config.toml']))
        self.assertEqual('ERROR: [traces_config_012] traces.toml key "device_pin" of trace ref_clk_to_device is FROM_DESIGN_REF_CLK_PORT; replace it with the name in your design or the part\'s datasheet\n', self.oStderr.getvalue())

    def test_an_spi_option_is_an_error(self):
        self.assertEqual(2, self.run_stacv(['create', 'template', 'rmii', '--mode', '0']))
        self.assertEqual('ERROR: [create_002] --mode is an option of the spi template, not of the rmii template\n', self.oStderr.getvalue())
