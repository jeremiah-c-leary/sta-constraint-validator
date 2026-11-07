import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sExampleDir = os.path.join(sProjectDir, 'example', 'spi_template')
FILE_NAMES = ['interface.toml', 'part.toml', 'traces.toml']


class SpiTemplateTestCase(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name

    def run_stacv(self, lArguments):
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv'] + lArguments):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def create_spi(self, iMode, lMoreArguments=None):
        lArguments = ['create', 'template', 'spi', '--wires', '4', '--mode', str(iMode), '--type', 'controller', '--output', self.sDirectory]
        if lMoreArguments is not None:
            lArguments.extend(lMoreArguments)
        return self.run_stacv(lArguments)

    def read_file(self, sFilename):
        with open(os.path.join(self.sDirectory, sFilename)) as oFile:
            return oFile.read()

    def read_lines(self, sFilename):
        return self.read_file(sFilename).split('\n')

    def fill_in_part(self):
        # The values a user fills in from the part's datasheet.
        sText = self.read_file('part.toml').replace('value = "FROM_DATASHEET"', 'value = 5').replace('source = "FROM_DATASHEET"', 'source = "Table 1"')
        with open(os.path.join(self.sDirectory, 'part.toml'), 'w') as oFile:
            oFile.write(sText)

    def run_in_directory(self, lArguments):
        sWorkingDir = os.getcwd()
        self.addCleanup(os.chdir, sWorkingDir)
        os.chdir(self.sDirectory)
        return self.run_stacv(lArguments)


class TestSpiTemplate(SpiTemplateTestCase):

    def test_mode_0_controller_is_the_example(self):
        self.assertEqual(0, self.create_spi(0))
        for sFilename in FILE_NAMES:
            with self.subTest(file=sFilename):
                with open(os.path.join(sExampleDir, sFilename)) as oFile:
                    self.assertEqual(oFile.read(), self.read_file(sFilename))

    def test_each_file_is_listed_as_it_is_created(self):
        self.assertEqual(0, self.create_spi(0))
        lExpected = []
        for sFilename in FILE_NAMES:
            lExpected.append(f'Creating template {os.path.join(self.sDirectory, sFilename)}')
        lExpected.append('')
        self.assertEqual('\n'.join(lExpected), self.oStdout.getvalue())

    def test_each_mode_sets_the_idle_level_and_the_edges(self):
        # Mode 1 gives the edges of the DAC81404 example.
        lModes = []
        lModes.append((0, 'low', 'device_clk", setup_edge = 4, hold_edge = 4', '"C", hold_edge = "A"', 'setup_edge = 1, hold_edge = 1', '"I", hold_edge = "A"', 'Rising', 'Falling'))
        lModes.append((1, 'low', 'device_clk", setup_edge = 8, hold_edge = 8', '"D", hold_edge = "B"', 'setup_edge = 2, hold_edge = 2', '"M", hold_edge = "E"', 'Falling', 'Rising'))
        lModes.append((2, 'high', 'device_clk", setup_edge = 8, hold_edge = 8', '"D", hold_edge = "B"', 'setup_edge = 2, hold_edge = 2', '"M", hold_edge = "E"', 'Falling', 'Rising'))
        lModes.append((3, 'high', 'device_clk", setup_edge = 4, hold_edge = 4', '"C", hold_edge = "A"', 'setup_edge = 1, hold_edge = 1', '"I", hold_edge = "A"', 'Rising', 'Falling'))
        for iMode, sIdle, sCopiLaunch, sCopiCapture, sCipoLaunch, sCipoCapture, sCaptureEdge, sLaunchEdge in lModes:
            with self.subTest(mode=iMode):
                oDirectory = tempfile.TemporaryDirectory()
                self.addCleanup(oDirectory.cleanup)
                self.sDirectory = oDirectory.name
                self.assertEqual(0, self.create_spi(iMode))
                sInterface = self.read_file('interface.toml')
                sPart = self.read_file('part.toml')
                self.assertIn(f'if_standard = "SPI mode {iMode}"', sInterface)
                self.assertIn(f'idle = "{sIdle}"', sInterface)
                self.assertIn(f'launch_clock = {{name = "{sCopiLaunch}}}', sInterface)
                self.assertIn(f'capture_clock = {{name = "spi_sck", setup_edge = {sCopiCapture}}}', sInterface)
                self.assertIn(f'launch_clock = {{name = "spi_sck", {sCipoLaunch}}}', sInterface)
                self.assertIn(f'capture_clock = {{name = "device_clk", setup_edge = {sCipoCapture}}}', sInterface)
                self.assertEqual(2, sPart.count(f'capture_edge = "{sCaptureEdge}"'))
                self.assertIn(f'launch_edge = "{sLaunchEdge}"', sPart)

    def test_every_mode_generates_constraints_once_the_part_is_filled_in(self):
        for iMode in range(4):
            with self.subTest(mode=iMode):
                oDirectory = tempfile.TemporaryDirectory()
                self.addCleanup(oDirectory.cleanup)
                self.sDirectory = oDirectory.name
                self.assertEqual(0, self.create_spi(iMode))
                self.fill_in_part()
                self.assertEqual(0, self.run_in_directory(['generate', 'xdc', 'interface.toml']))
                self.assertEqual('', self.oStderr.getvalue())

    def test_the_clock_periods_set_the_edges_and_the_frequency(self):
        # SCK is 80 ns, ten 8 ns device clock periods, so each SCK edge is ten device clock edges apart.
        self.assertEqual(0, self.create_spi(0, ['--clock-period', '8', '--sck-period', '80']))
        sInterface = self.read_file('interface.toml')
        self.assertIn('period = 8.000', sInterface)
        self.assertIn('period = 80.000', sInterface)
        self.assertIn('launch_clock = {name = "device_clk", setup_edge = 10, hold_edge = 10}', sInterface)
        self.assertIn('capture_clock = {name = "device_clk", setup_edge = "U", hold_edge = "A"}', sInterface)
        self.assertIn('clock = {pin = "SCK", max_frequency = 12.5}', self.read_file('part.toml'))
        self.assertIn('# Created by:  stacv create template spi --wires 4 --mode 0 --type controller --clock-period 8 --sck-period 80', sInterface)

    def test_the_timing_reports_are_named_by_interface_and_signal(self):
        self.assertEqual(0, self.create_spi(0))
        sInterface = self.read_file('interface.toml')
        for sSignal in ['COPI', 'CS', 'CIPO']:
            self.assertIn(f'    "timing_reports/SPI_INTERFACE_NAME.{sSignal}_timing.rpt",', sInterface)

    def test_a_value_still_to_fill_in_is_an_error(self):
        self.assertEqual(0, self.create_spi(0))
        self.assertEqual(2, self.run_in_directory(['generate', 'xdc', 'interface.toml']))
        self.assertEqual('ERROR: [part_config_011] part.toml key "value" in setup of pin COPI of interface SPI is FROM_DATASHEET; fill it in from the part\'s datasheet\n', self.oStderr.getvalue())


class TestSpiTemplateErrors(SpiTemplateTestCase):

    def assert_error(self, lArguments, sIdentifier, sMessage):
        self.assertEqual(2, self.run_stacv(lArguments))
        self.assertEqual(f'ERROR: [{sIdentifier}] {sMessage}\n', self.oStderr.getvalue())

    def test_an_existing_file_is_not_overwritten_and_nothing_is_written(self):
        sTraces = os.path.join(self.sDirectory, 'traces.toml')
        with open(sTraces, 'w') as oFile:
            oFile.write('filled in\n')
        self.assert_error(['create', 'template', 'spi', '--wires', '4', '--mode', '0', '--type', 'controller', '--output', self.sDirectory], 'create_001', f'{sTraces} already exists; the template is not written')
        self.assertEqual(['traces.toml'], os.listdir(self.sDirectory))

    def test_an_spi_option_on_another_template_is_an_error(self):
        self.assert_error(['create', 'template', 'interface', '--mode', '0'], 'create_002', '--mode is an option of the spi template, not of the interface template')

    def test_a_missing_spi_option_is_an_error(self):
        self.assert_error(['create', 'template', 'spi', '--wires', '4', '--type', 'controller'], 'create_003', 'the spi template needs --mode')

    def test_three_wires_is_not_supported_yet(self):
        self.assert_error(['create', 'template', 'spi', '--wires', '3', '--mode', '0', '--type', 'controller'], 'create_004', '--wires 3 is not supported yet; 3-wire SPI shares one data line, SDIO, in both directions')

    def test_a_peripheral_is_not_supported_yet(self):
        self.assert_error(['create', 'template', 'spi', '--wires', '4', '--mode', '0', '--type', 'peripheral'], 'create_004', '--type peripheral is not supported yet; the chip select of a peripheral is timed to a clock from the part')

    def test_sck_that_is_not_an_even_number_of_clock_periods_is_an_error(self):
        self.assert_error(['create', 'template', 'spi', '--wires', '4', '--mode', '0', '--type', 'controller', '--sck-period', '30'], 'create_005', '--sck-period 30 is not an even number of --clock-period 10; each edge of SCK is launched from a rising edge of the device clock')
