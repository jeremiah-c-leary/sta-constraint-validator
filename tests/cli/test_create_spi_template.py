import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sExampleDir = os.path.join(sProjectDir, 'example', 'spi_template')
FILE_NAMES = ['spi_config.toml', 'part.toml', 'traces.toml']
# The names a user fills in, in the order the SPI configuration asks for them.
DESIGN_NAMES = ['device_clk', 'O_SPI_SCK', 'q_spi_sck_reg', 'O_SPI_COPI', 'q_spi_copi_reg', 'I_SPI_CIPO', 'q_spi_cipo_reg', 'O_SPI_CS', 'q_spi_cs_reg']


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
        sText = sText.replace('max_frequency = "FROM_DATASHEET"', 'max_frequency = 50')
        with open(os.path.join(self.sDirectory, 'part.toml'), 'w') as oFile:
            oFile.write(sText)

    def fill_in_design(self):
        # The names a user fills in from the design.
        sText = self.read_file('spi_config.toml')
        for sName in DESIGN_NAMES:
            sText = sText.replace('"FROM_DESIGN"', f'"{sName}"', 1)
        with open(os.path.join(self.sDirectory, 'spi_config.toml'), 'w') as oFile:
            oFile.write(sText)

    def generate_interface(self):
        # The interface file the SPI configuration expands to.
        self.assertEqual(0, self.run_in_directory(['generate', 'interface', 'spi_config.toml']))
        return self.oStdout.getvalue()

    def run_in_directory(self, lArguments):
        sWorkingDir = os.getcwd()
        self.addCleanup(os.chdir, sWorkingDir)
        os.chdir(self.sDirectory)
        return self.run_stacv(lArguments)


class TestSpiTemplate(SpiTemplateTestCase):

    def test_mode_1_controller_is_the_example(self):
        self.assertEqual(0, self.create_spi(1))
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
                self.fill_in_design()
                sInterface = self.generate_interface()
                sPart = self.read_file('part.toml')
                self.assertIn(f'if_standard = "SPI mode {iMode}"', sInterface)
                self.assertIn(f'idle = "{sIdle}"', sInterface)
                self.assertIn(f'launch_clock = {{name = "{sCopiLaunch}}}', sInterface)
                self.assertIn(f'capture_clock = {{name = "O_SPI_SCK_clk", setup_edge = {sCopiCapture}}}', sInterface)
                self.assertIn(f'launch_clock = {{name = "O_SPI_SCK_clk", {sCipoLaunch}}}', sInterface)
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
                self.fill_in_design()
                self.fill_in_part()
                self.assertEqual(0, self.run_in_directory(['generate', 'xdc', 'spi_config.toml']))
                self.assertEqual('', self.oStderr.getvalue())

    def test_the_clock_periods_set_the_edges(self):
        # SCK is 80 ns, ten 8 ns device clock periods, so each SCK edge is ten device clock edges apart.
        self.assertEqual(0, self.create_spi(0, ['--clock-period', '8', '--sck-period', '80']))
        sConfig = self.read_file('spi_config.toml')
        self.assertIn('period = 8.0', sConfig)
        self.assertIn('period   = 80.0', sConfig)
        self.assertIn('# Created by:  stacv create template spi --wires 4 --mode 0 --type controller --clock-period 8 --sck-period 80', sConfig)
        self.fill_in_design()
        sInterface = self.generate_interface()
        self.assertIn('launch_clock = {name = "device_clk", setup_edge = 10, hold_edge = 10}', sInterface)
        self.assertIn('capture_clock = {name = "device_clk", setup_edge = "U", hold_edge = "A"}', sInterface)

    def test_the_timing_reports_are_named_by_interface_and_signal(self):
        self.assertEqual(0, self.create_spi(0))
        self.fill_in_design()
        sInterface = self.generate_interface()
        for sSignal in ['COPI', 'CS', 'CIPO']:
            self.assertIn(f'    "timing_reports/SPI.{sSignal}_timing.rpt",', sInterface)

    def test_a_name_still_to_fill_in_is_an_error(self):
        self.assertEqual(0, self.create_spi(0))
        self.assertEqual(2, self.run_in_directory(['generate', 'xdc', 'spi_config.toml']))
        self.assertEqual('ERROR: [spi_config_006] spi_config.toml key "name" in [device_clock] (line 36) is FROM_DESIGN; replace it with the name in your design\n', self.oStderr.getvalue())

    def test_a_value_still_to_fill_in_is_an_error(self):
        self.assertEqual(0, self.create_spi(0))
        self.fill_in_design()
        self.assertEqual(2, self.run_in_directory(['generate', 'xdc', 'spi_config.toml']))
        self.assertEqual('ERROR: [part_config_011] part.toml key "max_frequency" in clock of pin COPI of interface SPI is FROM_DATASHEET; fill it in from the part\'s datasheet\n', self.oStderr.getvalue())


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
