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
# The edges of the fixture, as the keys write them.
EDGES = {}
EDGES['launch'] = ('{sck_edge = "change", clocks = 0, ', 'launch   = ')
EDGES['capture'] = ('{sck_edge = "sample", clocks = 0, ', 'capture  = ')
EDGES['assert'] = ('{sck_edge = "first sample", clocks = -4, ', 'assert   = ')
EDGES['deassert'] = ('{sck_edge = "last change", clocks = 4, ', 'deassert = ')


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

    def set_edge(self, sKey, sSckEdge, sClocks):
        # Changes where an edge is counted from, and how many device clocks, keeping its source.
        sOldStart, sKeyText = EDGES[sKey]
        self.edit_config(sKeyText + sOldStart, f'{sKeyText}{{sck_edge = "{sSckEdge}", clocks = {sClocks}, ')

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

    def test_the_edges_are_counted_from_the_sck_edges_they_name(self):
        # CS is asserted 4 clocks, 8 edges, before the first sample edge at 16, and deasserted 8 edges after the last
        # change edge at 8.
        sInterface = self.generate_interface()
        self.assertIn('launch_clock = {name = "sys_clk", setup_edge = 8, hold_edge = 8}\ncapture_clock = {name = "dac_sclk_clk", setup_edge = "C", hold_edge = "A"}\nregisters = ["u_spi/sdi_q_reg"]', sInterface)
        self.assertIn('launch_clock = {name = "sys_clk", setup_edge = 8, hold_edge = 16}\ncapture_clock = {name = "dac_sclk_clk", setup_edge = "C", hold_edge = "A"}\nregisters = ["u_spi/scs_n_q_reg"]', sInterface)
        self.assertIn('launch_clock = {name = "dac_sclk_clk", setup_edge = 1, hold_edge = 1}\ncapture_clock = {name = "sys_clk", setup_edge = "Q", hold_edge = "A"}\nregisters = ["u_spi/rx_shift_reg[0]"]', sInterface)

    def test_copi_launch_counts_device_clocks_from_the_change_edge(self):
        self.set_edge('launch', 'change', '1')
        self.assertIn('launch_clock = {name = "sys_clk", setup_edge = 10, hold_edge = 10}', self.generate_interface())

    def test_cipo_capture_counts_device_clocks_from_the_sample_edge(self):
        # CIPO is captured on the device clock, so its edge moves the captures and not the part's launch.
        self.set_edge('capture', 'sample', '1')
        sInterface = self.generate_interface()
        self.assertIn('launch_clock = {name = "dac_sclk_clk", setup_edge = 1, hold_edge = 1}\ncapture_clock = {name = "sys_clk", setup_edge = "S", hold_edge = "C"}', sInterface)

    def test_cs_deassert_can_count_from_the_last_sample_edge(self):
        # 8 clocks after the last sample edge at edge 0 is the same edge 16 as 4 clocks after the last change edge.
        self.set_edge('deassert', 'last sample', '8')
        self.assertIn('launch_clock = {name = "sys_clk", setup_edge = 8, hold_edge = 16}', self.generate_interface())

    def test_half_a_clock_is_a_falling_edge_of_the_device_clock(self):
        self.set_edge('launch', 'change', '0.5')
        self.assertIn('setup_edge = 9, hold_edge = 9', self.generate_interface())

    def test_the_timing_reports_are_named_by_interface_and_signal_in_the_folder_given(self):
        sInterface = self.generate_interface()
        for sSignal in ['COPI', 'CS', 'CIPO']:
            self.assertIn(f'timing_reports = [\n    "timing_reports/DAC_SPI.{sSignal}_timing.rpt",\n]', sInterface)

    def test_the_interface_file_says_where_the_edges_come_from(self):
        sInterface = self.generate_interface()
        self.assertIn('# Generated from spi_config.toml by:  stacv generate interface spi_config.toml\n', sInterface)
        lExpected = []
        lExpected.append('# Edges:  set in the SPI configuration, not verified against simulation')
        lExpected.append('#         COPI launch   at the SCK change edge                     spi_master.vhd: SCLK_HIGH sets sdi_q with sclk_q low')
        lExpected.append('#         CIPO capture  at the SCK sample edge                     spi_master.vhd: SCLK_LOW shifts sdo into rx_shift with sclk_q high')
        lExpected.append('#         CS assert     4 clocks before the first SCK sample edge  spi_master.vhd: IDLE clears scs_n_q with the first bit, HALF_PERIOD before sclk_q rises')
        lExpected.append('#         CS deassert   4 clocks after the last SCK change edge    spi_master.vhd: TRAIL sets scs_n_q HALF_PERIOD after the last sclk_q fall')
        self.assertIn('\n'.join(lExpected) + '\n', sInterface)

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
        lExpected = []
        lExpected.append('# Edges:      set in the SPI configuration, not verified against simulation')
        lExpected.append('#             COPI launch   at the SCK change edge                     spi_master.vhd: SCLK_HIGH sets sdi_q with sclk_q low')
        lExpected.append('#             CIPO capture  at the SCK sample edge                     spi_master.vhd: SCLK_LOW shifts sdo into rx_shift with sclk_q high')
        lExpected.append('#             CS assert     4 clocks before the first SCK sample edge  spi_master.vhd: IDLE clears scs_n_q with the first bit, HALF_PERIOD before sclk_q rises')
        lExpected.append('#             CS deassert   4 clocks after the last SCK change edge    spi_master.vhd: TRAIL sets scs_n_q HALF_PERIOD after the last sclk_q fall')
        self.assertIn('\n' + '\n'.join(lExpected) + '\n', sXdc)

    def test_one_clock_is_written_in_the_singular(self):
        self.set_edge('launch', 'change', '-1')
        self.assertIn('COPI launch   1 clock before the SCK change edge', self.generate_interface())

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
        self.assert_error('spi_config_002', 'missing required key "register" in [copi] (line 39)')

    def test_a_missing_table_is_an_error(self):
        self.edit_config('[cipo]\nport     = "dac_sdo"\nregister = "u_spi/rx_shift_reg[0]"\ncapture  = {sck_edge = "sample", clocks = 0, source = "spi_master.vhd: SCLK_LOW shifts sdo into rx_shift with sclk_q high"}\n', '')
        self.assert_error('spi_config_002', 'missing required key "cipo"')

    def test_an_edge_that_is_not_a_table_is_an_error(self):
        self.edit_config('assert   = {sck_edge = "first sample", clocks = -4, source = "spi_master.vhd: IDLE clears scs_n_q with the first bit, HALF_PERIOD before sclk_q rises"}', 'assert   = -4')
        self.assert_error('spi_config_003', 'key "assert" in [cs] (line 54) must be a table')

    def test_a_misspelled_key_is_an_error(self):
        self.edit_config('deassert = {', 'dessert = {')
        self.assert_error('spi_config_004', 'key "dessert" in [cs] (line 51) is not a key stacv reads; the keys are port, register, assert, deassert')

    def test_a_misspelled_key_of_an_edge_is_an_error(self):
        self.edit_config('{sck_edge = "change", clocks = 0, ', '{sck_edge = "change", clock = 0, ')
        self.assert_error('spi_config_004', 'key "clock" in [copi] (line 42) is not a key stacv reads; the keys are sck_edge, clocks, source')

    def test_an_edge_without_a_source_is_an_error(self):
        self.edit_config(', source = "spi_master.vhd: SCLK_HIGH sets sdi_q with sclk_q low"}', '}')
        self.assert_error('spi_config_002', 'missing required key "source" in [copi] (line 42)')

    def test_an_edge_whose_source_is_still_to_fill_in_is_an_error(self):
        self.edit_config('source = "spi_master.vhd: SCLK_HIGH sets sdi_q with sclk_q low"', 'source = "FROM_DESIGN"')
        self.assert_error('spi_config_006', 'key "launch" in [copi] (line 42) has source FROM_DESIGN; say where in the design the edge comes from')

    def test_an_sck_edge_the_key_is_not_counted_from_is_an_error(self):
        self.set_edge('deassert', 'first sample', '4')
        self.assert_error('spi_config_014', 'key "deassert" in [cs] (line 55) has sck_edge "first sample"; it must be "last change" or "last sample"')

    def test_clocks_that_are_not_a_whole_or_half_number_is_an_error(self):
        self.set_edge('launch', 'change', '0.25')
        self.assert_error('spi_config_015', 'key "launch" in [copi] (line 42) has clocks 0.25; an edge is on a device clock edge, so clocks is a whole or half number')

    def test_an_interface_stacv_has_no_configuration_for_is_an_error(self):
        self.edit_config('interface = "spi"', 'interface = "i2c"')
        self.assert_error('spi_config_005', 'key "interface" (line 17) names i2c, which stacv has no configuration for; the configurations are spi')

    def test_a_name_still_to_fill_in_is_an_error(self):
        self.edit_config('port     = "dac_sdo"', 'port     = "FROM_DESIGN"')
        self.assert_error('spi_config_006', 'key "port" in [cipo] (line 46) is FROM_DESIGN; replace it with the name in your design')

    def test_a_mode_that_is_not_an_spi_mode_is_an_error(self):
        self.edit_config('mode      = 0', 'mode      = 4')
        self.assert_error('spi_config_007', 'key "mode" (line 19) must be 0, 1, 2 or 3')

    def test_a_peripheral_is_not_supported_yet(self):
        self.edit_config('role      = "controller"', 'role      = "peripheral"')
        self.assert_error('spi_config_008', 'key "role" (line 20) must be "controller"; a peripheral is not supported yet')

    def test_a_period_that_is_not_greater_than_0_is_an_error(self):
        self.edit_config('period = 10.0', 'period = 0')
        self.assert_error('spi_config_009', 'key "period" in [device_clock] (line 30) must be greater than 0')

    def test_sck_that_is_not_an_even_number_of_device_clock_periods_is_an_error(self):
        self.edit_config('period   = 80.0', 'period   = 30.0')
        self.assert_error('spi_config_010', 'key "period" in [sck] (line 36) is 30 ns, which is not an even number of device clock periods of 10 ns; each edge of SCK is launched from a rising edge of the device clock')

    def test_copi_launched_at_or_after_the_edge_that_samples_it_is_an_error(self):
        self.set_edge('launch', 'change', '4')
        self.assert_error('spi_config_011', 'key "launch" in [copi] (line 42) puts the launch at edge 16, at or after the rising edge of SCK at edge 16 that samples it')

    def test_copi_launched_before_the_edge_that_samples_the_bit_before_it_is_an_error(self):
        self.set_edge('launch', 'change', '-4.5')
        self.assert_error('spi_config_011', 'key "launch" in [copi] (line 42) puts the launch at edge -1, before the rising edge of SCK at edge 0 that samples the bit before it')

    def test_cs_asserted_before_edge_0_is_an_error(self):
        self.set_edge('assert', 'first sample', '-8.5')
        self.assert_error('spi_config_011', 'key "assert" in [cs] (line 54) puts the launch at edge -1, before edge 0')

    def test_cs_asserted_at_or_after_the_first_sample_edge_is_an_error(self):
        self.set_edge('assert', 'first sample', '0')
        self.assert_error('spi_config_011', 'key "assert" in [cs] (line 54) puts the launch at edge 16, at or after the first rising edge of SCK at edge 16')

    def test_cs_deasserted_before_the_last_sample_edge_is_an_error(self):
        self.set_edge('deassert', 'last change', '-4.5')
        self.assert_error('spi_config_011', 'key "deassert" in [cs] (line 55) puts the launch at edge -1, before the last rising edge of SCK at edge 0')

    def test_cs_deasserted_long_after_the_last_sample_edge_is_not_an_error(self):
        # SCK has stopped, so nothing limits how late CS is deasserted.
        self.set_edge('deassert', 'last change', '500')
        self.assertIn('setup_edge = 8, hold_edge = 1008', self.generate_interface())

    def test_cipo_captured_before_edge_a_is_an_error(self):
        self.set_edge('capture', 'sample', '-0.5')
        self.assert_error('spi_config_011', 'key "capture" in [cipo] (line 48) puts the hold capture before edge A, the first edge')

    def test_cipo_held_after_the_edge_that_launches_it_is_an_error(self):
        self.set_edge('capture', 'sample', '4.5')
        self.assert_error('spi_config_011', 'key "capture" in [cipo] (line 48) puts the hold capture at edge J, after the falling edge of SCK at edge I that launches CIPO')

    def test_cipo_set_up_at_or_before_the_edge_that_launches_it_is_an_error(self):
        # In mode 1 the part launches CIPO on the rising edge at edge 16, and the device captures it at edge 24.
        self.edit_file('part.toml', 'if_standard = "SPI mode 0"', 'if_standard = "SPI mode 1"')
        self.edit_config('mode      = 0', 'mode      = 1')
        self.set_edge('capture', 'sample', '-4')
        self.assert_error('spi_config_011', 'key "capture" in [cipo] (line 48) puts the setup capture at edge Q, at or before the rising edge of SCK at edge Q that launches CIPO')

    def test_a_part_without_the_spi_interface_of_the_mode_is_an_error(self):
        self.edit_file('part.toml', 'if_standard = "SPI mode 0"', 'if_standard = "SPI mode 1"')
        self.assert_error('spi_config_012', 'key "part" (line 22) names part.toml, which has no [[interface]] with if_standard "SPI mode 0" and if_role "peripheral"')

    def test_a_part_with_two_spi_interfaces_of_the_mode_is_an_error(self):
        with open('part.toml', 'a') as oFile:
            oFile.write('\n[[interface]]\nname = "Second SPI"\nif_standard = "SPI mode 0"\nif_role = "peripheral"\n')
        self.assert_error('spi_config_013', 'key "part" (line 22) names part.toml, which has more than one [[interface]] with if_standard "SPI mode 0" and if_role "peripheral": Serial Programming Interface, Second SPI')

    def test_an_interface_file_does_not_generate_an_interface_file(self):
        self.assertEqual(2, self.run_stacv(['generate', 'interface', sDac81404Interface]))
        self.assertEqual(f'ERROR: [generate_012] {sDac81404Interface} is an interface file, not an interface configuration file; only an interface configuration file, such as spi_config.toml, generates an interface file\n', self.oStderr.getvalue())


class TestSpiConfigReadClock(SpiConfigTestCase):
    '''
    The DAC81404 example, SPI mode 1 with SCK 40 ns for writes and 80 ns for reads, as an SPI configuration.  Its
    expansion is compared with the example's hand-written interface file.
    '''

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = os.path.join(oTemporaryDirectory.name, 'dac81404')
        shutil.copytree(os.path.join(os.path.dirname(__file__), 'fixtures', 'dac81404_spi_config'), self.sDirectory)
        sWorkingDir = os.getcwd()
        self.addCleanup(os.chdir, sWorkingDir)
        os.chdir(self.sDirectory)

    def test_the_read_period_adds_a_read_clock_on_the_sck_port(self):
        sInterface = self.generate_interface()
        self.assertIn('[[clock]]\nname = "O_DAC_SCLK_rd_clk"\nport = "O_DAC_SCLK"\ngenerator = {source = "q_spi_output_clock_reg", master_pin = "C", target_pin = "Q", master_clock = "clk_100mhz"}\nperiod = 80.000\n', sInterface)

    def test_the_edges_are_those_of_the_hand_written_interface_file(self):
        sInterface = self.generate_interface()
        self.assertIn('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 8}\ncapture_clock = {name = "O_DAC_SCLK_clk", setup_edge = "D", hold_edge = "B"}\nregisters = ["q_spi_output_data_reg"]', sInterface)
        self.assertIn('launch_clock = {name = "clk_100mhz", setup_edge = 4, hold_edge = 8}\ncapture_clock = {name = "O_DAC_SCLK_clk", setup_edge = "D", hold_edge = "B"}\nregisters = ["q_spi_sden_f_reg"]', sInterface)

    def test_cipo_is_launched_on_the_read_clock_and_captured_from_its_edges(self):
        sInterface = self.generate_interface()
        self.assertIn('launch_clock = {name = "O_DAC_SCLK_rd_clk", setup_edge = 2, hold_edge = 2}\ncapture_clock = {name = "clk_100mhz", setup_edge = "AC", hold_edge = "M"}', sInterface)

    def test_the_constraints_add_the_read_clock_to_the_sck_register(self):
        self.assertEqual(0, self.run_stacv(['generate', 'xdc', 'spi_config.toml']))
        sXdc = self.oStdout.getvalue()
        self.assertIn('create_generated_clock -add -master_clock [get_clocks clk_100mhz] -name O_DAC_SCLK_rd_clk -source [get_pins q_spi_output_clock_reg/C] -divide_by 8 [get_pins q_spi_output_clock_reg/Q]', sXdc)
        self.assertIn('set_multicycle_path 6 -setup -end -from [get_ports I_DAC_DATA] -to [get_clocks clk_100mhz]', sXdc)

    def test_a_read_period_that_is_not_an_even_number_of_device_clock_periods_is_an_error(self):
        self.edit_config('read_period = 80.0', 'read_period = 70.0')
        self.assertEqual(2, self.run_stacv(['generate', 'interface', 'spi_config.toml']))
        self.assertEqual('ERROR: [spi_config_010] spi_config.toml key "read_period" in [sck] (line 21) is 70 ns, which is not an even number of device clock periods of 10 ns; each edge of SCK is launched from a rising edge of the device clock\n', self.oStderr.getvalue())

    def test_a_cipo_capture_at_the_read_clock_edge_that_launches_it_is_an_error(self):
        # The read SCK's change edge, which launches CIPO, is at device clock edge 16, Q; the write SCK's is at 8.
        self.edit_config('clocks = 2, source = "DAC81404', 'clocks = -4, source = "DAC81404')
        self.assertEqual(2, self.run_stacv(['generate', 'interface', 'spi_config.toml']))
        self.assertEqual('ERROR: [spi_config_011] spi_config.toml key "capture" in [cipo] (line 31) puts the setup capture at edge Q, at or before the rising edge of SCK at edge Q that launches CIPO\n', self.oStderr.getvalue())
