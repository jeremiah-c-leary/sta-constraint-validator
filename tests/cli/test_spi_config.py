import contextlib
import io
import os
import shutil
import tempfile
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sFixtureDir = os.path.join(os.path.dirname(__file__), 'fixtures', 'dac39rf20_spi_config')
sDac81404Interface = os.path.join(sProjectDir, 'example', 'texas_instruments', 'DAC81404', 'interface.toml')
COPI_REGISTER = 'register = "u_spi/sdi_q_reg"'
CIPO_REGISTER = 'register = "u_spi/rx_shift_reg[0]"'


class SpiConfigTestCase(unittest.TestCase):
    '''
    The DAC39RF20 start-up design: SPI mode 0, SCK 80 ns from a 10 ns device clock, so each SCK edge is 8 device clock
    edges apart, and CS moved 8 edges later at both ends.  The timing reports are from that design in Vivado.
    '''

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = os.path.join(oTemporaryDirectory.name, 'dac39rf20')
        shutil.copytree(sFixtureDir, self.sDirectory)
        sWorkingDir = os.getcwd()
        self.addCleanup(os.chdir, sWorkingDir)
        os.chdir(self.sDirectory)

    def run_stacv(self, lArguments):
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv'] + lArguments):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def edit_file(self, sFilename, sOld, sNew):
        with open(sFilename) as oFile:
            sText = oFile.read()
        self.assertIn(sOld, sText)
        with open(sFilename, 'w') as oFile:
            oFile.write(sText.replace(sOld, sNew, 1))

    def edit_config(self, sOld, sNew):
        self.edit_file('spi_config.toml', sOld, sNew)

    def generate_interface(self):
        self.assertEqual(0, self.run_stacv(['generate', 'interface', 'spi_config.toml']))
        return self.oStdout.getvalue()


class TestSpiConfig(SpiConfigTestCase):

    def test_check_passes_on_the_timing_reports_of_the_design(self):
        self.assertEqual(0, self.run_stacv(['check', 'spi_config.toml']))
        sOutput = self.oStdout.getvalue()
        for sPort in ['dac_sdi.SDR-SS-O', 'dac_scs_n.SDR-SS-O-FLC', 'dac_sdo.SDR-SS-RT-DI']:
            self.assertIn(f'PASSED: {sPort}\n', sOutput)
        self.assertIn('Check Passed', sOutput)

    def test_the_interface_uses_the_names_in_the_design(self):
        sInterface = self.generate_interface()
        self.assertIn('name = "DAC_SPI"\n', sInterface)
        self.assertIn('part_interface = "Serial Programming Interface"\n', sInterface)
        self.assertIn('[[clock]]\nname = "sys_clk"\nperiod = 10.000\n', sInterface)
        self.assertIn('name = "dac_sclk_clk"\nport = "dac_sclk"\ngenerator = {source = "u_spi/sclk_q_reg", master_pin = "C", target_pin = "Q", master_clock = "sys_clk"}\nperiod = 80.000\nidle = "low"\n', sInterface)
        self.assertIn('name = "dac_sdi"\nmethodology = "SDR-SS-O"\n', sInterface)
        self.assertIn('registers = ["u_spi/sdi_q_reg"]\n', sInterface)
        self.assertIn('name = "dac_scs_n"\nmethodology = "SDR-SS-O-FLC"\n', sInterface)
        self.assertIn('name = "dac_sdo"\nmethodology = "SDR-SS-RT-DI"\n', sInterface)
        self.assertIn('registers = ["u_spi/rx_shift_reg[0]"]\n', sInterface)

    def test_the_mode_sets_the_edges_and_the_adjusts_move_them(self):
        # CS is set at edge 0 and cleared at edge 8 in mode 0; the design moves both 8 edges later.
        sInterface = self.generate_interface()
        self.assertIn('launch_clock = {name = "sys_clk", setup_edge = 8, hold_edge = 8}\ncapture_clock = {name = "dac_sclk_clk", setup_edge = "C", hold_edge = "A"}\nregisters = ["u_spi/sdi_q_reg"]', sInterface)
        self.assertIn('launch_clock = {name = "sys_clk", setup_edge = 8, hold_edge = 16}\ncapture_clock = {name = "dac_sclk_clk", setup_edge = "C", hold_edge = "A"}\nregisters = ["u_spi/scs_n_q_reg"]', sInterface)
        self.assertIn('launch_clock = {name = "dac_sclk_clk", setup_edge = 1, hold_edge = 1}\ncapture_clock = {name = "sys_clk", setup_edge = "Q", hold_edge = "A"}\nregisters = ["u_spi/rx_shift_reg[0]"]', sInterface)

    def test_the_copi_adjust_moves_its_launch(self):
        self.edit_config(COPI_REGISTER, COPI_REGISTER + '\nadjust = 2')
        self.assertIn('launch_clock = {name = "sys_clk", setup_edge = 10, hold_edge = 10}', self.generate_interface())

    def test_the_cipo_adjust_moves_its_captures(self):
        # CIPO is captured on the device clock, so its adjust moves the captures and not the part's launch.
        self.edit_config(CIPO_REGISTER, CIPO_REGISTER + '\nadjust = 2')
        sInterface = self.generate_interface()
        self.assertIn('launch_clock = {name = "dac_sclk_clk", setup_edge = 1, hold_edge = 1}\ncapture_clock = {name = "sys_clk", setup_edge = "S", hold_edge = "C"}', sInterface)

    def test_the_cs_adjusts_left_out_are_the_mode_edges(self):
        self.edit_config('setup_adjust = 8\nhold_adjust  = 8\n', '')
        self.assertIn('launch_clock = {name = "sys_clk", setup_edge = 0, hold_edge = 8}', self.generate_interface())

    def test_the_timing_reports_are_named_by_interface_and_signal_in_the_folder_given(self):
        sInterface = self.generate_interface()
        for sSignal in ['COPI', 'CS', 'CIPO']:
            self.assertIn(f'timing_reports = [\n    "timing_reports/DAC_SPI.{sSignal}_timing.rpt",\n]', sInterface)

    def test_the_interface_file_says_where_the_edges_come_from(self):
        sInterface = self.generate_interface()
        self.assertIn('# Generated from spi_config.toml by:  stacv generate interface spi_config.toml\n', sInterface)
        self.assertIn('# Edges:  SPI mode 0 defaults; CS setup +8, hold +8; not verified against simulation\n', sInterface)

    def test_the_interface_file_is_written_to_the_output(self):
        self.assertEqual(0, self.run_stacv(['generate', 'interface', 'spi_config.toml', '--output', 'interface.toml']))
        self.assertEqual('Creating interface file interface.toml\n', self.oStdout.getvalue())
        with open('interface.toml') as oFile:
            self.assertIn('name = "DAC_SPI"\n', oFile.read())

    def test_the_generated_interface_file_is_an_interface_file(self):
        # The file a user takes over gives the same check as the configuration.
        self.assertEqual(0, self.run_stacv(['generate', 'interface', 'spi_config.toml', '--output', 'interface.toml']))
        self.assertEqual(0, self.run_stacv(['check', 'interface.toml']))
        self.assertIn('Check Passed', self.oStdout.getvalue())

    def test_the_constraints_list_the_configuration_and_the_edges(self):
        self.assertEqual(0, self.run_stacv(['generate', 'xdc', 'spi_config.toml']))
        sXdc = self.oStdout.getvalue()
        self.assertRegex(sXdc, r'\n# [0-9a-f]{32}  spi_config.toml\n')
        self.assertIn('\n# Edges:      SPI mode 0 defaults; CS setup +8, hold +8; not verified against simulation\n', sXdc)

    def test_the_edges_line_lists_each_adjust_given(self):
        self.edit_config(COPI_REGISTER, COPI_REGISTER + '\nadjust = 2')
        self.edit_config(CIPO_REGISTER, CIPO_REGISTER + '\nadjust = -0')
        self.edit_config('setup_adjust = 8', 'setup_adjust = 0')
        self.assertEqual(0, self.run_stacv(['generate', 'xdc', 'spi_config.toml']))
        self.assertIn('\n# Edges:      SPI mode 0 defaults; COPI +2; CS hold +8; not verified against simulation\n', self.oStdout.getvalue())

    def test_the_edges_line_without_adjusts_names_the_defaults_only(self):
        self.edit_config('setup_adjust = 8\nhold_adjust  = 8\n', '')
        self.assertEqual(0, self.run_stacv(['generate', 'xdc', 'spi_config.toml']))
        self.assertIn('\n# Edges:      SPI mode 0 defaults; not verified against simulation\n', self.oStdout.getvalue())

    def test_the_report_script_writes_the_reports_check_reads(self):
        self.assertEqual(0, self.run_stacv(['generate', 'report_tcl', 'spi_config.toml']))
        sScript = self.oStdout.getvalue()
        for sSignal in ['COPI', 'CS', 'CIPO']:
            self.assertIn(f'timing_reports/DAC_SPI.{sSignal}_timing.rpt', sScript)

    def test_the_edges_are_drawn_without_the_part_and_traces_files(self):
        os.remove('part.toml')
        os.remove('traces.toml')
        self.assertEqual(0, self.run_stacv(['visualize', 'edges', 'spi_config.toml']))
        self.assertIn('Port:  dac_scs_n', self.oStdout.getvalue())

    def test_the_block_diagram_uses_the_names_in_the_design(self):
        self.assertEqual(0, self.run_stacv(['visualize', 'block_diagram', 'spi_config.toml']))
        self.assertIn('[u_spi/scs_n_q_reg]', self.oStdout.getvalue())


class TestSpiConfigErrors(SpiConfigTestCase):

    def assert_error(self, sIdentifier, sMessage):
        self.assertEqual(2, self.run_stacv(['generate', 'interface', 'spi_config.toml']))
        self.assertEqual(f'ERROR: [{sIdentifier}] spi_config.toml {sMessage}\n', self.oStderr.getvalue())

    def test_a_missing_key_is_reported_at_its_table(self):
        self.edit_config(COPI_REGISTER + '\n', '')
        self.assert_error('spi_config_002', 'missing required key "register" in [copi] (line 40)')

    def test_a_missing_table_is_an_error(self):
        self.edit_config('[cipo]\nport     = "dac_sdo"\nregister = "u_spi/rx_shift_reg[0]"\n', '')
        self.assert_error('spi_config_002', 'missing required key "cipo"')

    def test_an_adjust_that_is_not_a_whole_number_is_an_error(self):
        self.edit_config('setup_adjust = 8', 'setup_adjust = 1.5')
        self.assert_error('spi_config_003', 'key "setup_adjust" in [cs] (line 56) must be a whole number')

    def test_a_misspelled_key_is_an_error(self):
        self.edit_config('hold_adjust  = 8', 'hold_ajust  = 8')
        self.assert_error('spi_config_004', 'key "hold_ajust" in [cs] (line 53) is not a key stacv reads; the keys are port, register, setup_adjust, hold_adjust')

    def test_an_interface_stacv_has_no_configuration_for_is_an_error(self):
        self.edit_config('interface = "spi"', 'interface = "i2c"')
        self.assert_error('spi_config_005', 'key "interface" (line 18) names i2c, which stacv has no configuration for; the configurations are spi')

    def test_a_name_still_to_fill_in_is_an_error(self):
        self.edit_config('port     = "dac_sdo"', 'port     = "FROM_DESIGN"')
        self.assert_error('spi_config_006', 'key "port" in [cipo] (line 46) is FROM_DESIGN; replace it with the name in your design')

    def test_a_mode_that_is_not_an_spi_mode_is_an_error(self):
        self.edit_config('mode      = 0', 'mode      = 4')
        self.assert_error('spi_config_007', 'key "mode" (line 20) must be 0, 1, 2 or 3')

    def test_a_peripheral_is_not_supported_yet(self):
        self.edit_config('role      = "controller"', 'role      = "peripheral"')
        self.assert_error('spi_config_008', 'key "role" (line 21) must be "controller"; a peripheral is not supported yet')

    def test_a_period_that_is_not_greater_than_0_is_an_error(self):
        self.edit_config('period = 10.0', 'period = 0')
        self.assert_error('spi_config_009', 'key "period" in [device_clock] (line 31) must be greater than 0')

    def test_sck_that_is_not_an_even_number_of_device_clock_periods_is_an_error(self):
        self.edit_config('period   = 80.0', 'period   = 30.0')
        self.assert_error('spi_config_010', 'key "period" in [sck] (line 37) is 30 ns, which is not an even number of device clock periods of 10 ns; each edge of SCK is launched from a rising edge of the device clock')

    def test_copi_launched_at_or_after_the_edge_that_samples_it_is_an_error(self):
        self.edit_config(COPI_REGISTER, COPI_REGISTER + '\nadjust = 8')
        self.assert_error('spi_config_011', 'key "adjust" in [copi] (line 43) moves the launch to edge 16, at or after the rising edge of SCK at edge 16 that samples it')

    def test_copi_launched_before_the_edge_that_samples_the_bit_before_it_is_an_error(self):
        self.edit_config(COPI_REGISTER, COPI_REGISTER + '\nadjust = -9')
        self.assert_error('spi_config_011', 'key "adjust" in [copi] (line 43) moves the launch to edge -1, before the rising edge of SCK at edge 0 that samples the bit before it')

    def test_cs_set_before_edge_0_is_an_error(self):
        self.edit_config('setup_adjust = 8', 'setup_adjust = -1')
        self.assert_error('spi_config_011', 'key "setup_adjust" in [cs] (line 56) moves the launch to edge -1, before edge 0')

    def test_cs_set_at_or_after_the_first_sample_edge_is_an_error(self):
        self.edit_config('setup_adjust = 8', 'setup_adjust = 16')
        self.assert_error('spi_config_011', 'key "setup_adjust" in [cs] (line 56) moves the launch to edge 16, at or after the first rising edge of SCK at edge 16')

    def test_cs_cleared_before_the_last_sample_edge_is_an_error(self):
        self.edit_config('hold_adjust  = 8', 'hold_adjust  = -9')
        self.assert_error('spi_config_011', 'key "hold_adjust" in [cs] (line 57) moves the launch to edge -1, before the last rising edge of SCK at edge 0')

    def test_cs_cleared_long_after_the_last_sample_edge_is_not_an_error(self):
        # SCK has stopped, so nothing limits how late CS is cleared.
        self.edit_config('hold_adjust  = 8', 'hold_adjust  = 1000')
        self.assertIn('setup_edge = 8, hold_edge = 1008', self.generate_interface())

    def test_an_odd_adjust_is_not_an_error(self):
        # A design can launch on the falling edge of the device clock.
        self.edit_config(COPI_REGISTER, COPI_REGISTER + '\nadjust = 1')
        self.assertIn('setup_edge = 9, hold_edge = 9', self.generate_interface())

    def test_cipo_captured_before_edge_a_is_an_error(self):
        self.edit_config(CIPO_REGISTER, CIPO_REGISTER + '\nadjust = -1')
        self.assert_error('spi_config_011', 'key "adjust" in [cipo] (line 48) moves the hold capture before edge A, the first edge')

    def test_cipo_held_after_the_edge_that_launches_it_is_an_error(self):
        self.edit_config(CIPO_REGISTER, CIPO_REGISTER + '\nadjust = 9')
        self.assert_error('spi_config_011', 'key "adjust" in [cipo] (line 48) moves the hold capture to edge J, after the falling edge of SCK at edge I that launches CIPO')

    def test_cipo_set_up_at_or_before_the_edge_that_launches_it_is_an_error(self):
        # In mode 1 the part launches CIPO on the rising edge at edge 16, and the device captures it at edge 24.
        self.edit_file('part.toml', 'if_standard = "SPI mode 0"', 'if_standard = "SPI mode 1"')
        self.edit_config('mode      = 0', 'mode      = 1')
        self.edit_config(CIPO_REGISTER, CIPO_REGISTER + '\nadjust = -8')
        self.assert_error('spi_config_011', 'key "adjust" in [cipo] (line 48) moves the setup capture to edge Q, at or before the rising edge of SCK at edge Q that launches CIPO')

    def test_a_part_without_the_spi_interface_of_the_mode_is_an_error(self):
        self.edit_file('part.toml', 'if_standard = "SPI mode 0"', 'if_standard = "SPI mode 1"')
        self.assert_error('spi_config_012', 'key "part" (line 23) names part.toml, which has no [[interface]] with if_standard "SPI mode 0" and if_role "peripheral"')

    def test_a_part_with_two_spi_interfaces_of_the_mode_is_an_error(self):
        with open('part.toml', 'a') as oFile:
            oFile.write('\n[[interface]]\nname = "Second SPI"\nif_standard = "SPI mode 0"\nif_role = "peripheral"\n')
        self.assert_error('spi_config_013', 'key "part" (line 23) names part.toml, which has more than one [[interface]] with if_standard "SPI mode 0" and if_role "peripheral": Serial Programming Interface, Second SPI')

    def test_an_interface_file_does_not_generate_an_interface_file(self):
        self.assertEqual(2, self.run_stacv(['generate', 'interface', sDac81404Interface]))
        self.assertEqual(f'ERROR: [generate_012] {sDac81404Interface} is an interface file, not an interface configuration file; only an interface configuration file, such as spi_config.toml, generates an interface file\n', self.oStderr.getvalue())
