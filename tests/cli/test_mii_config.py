import os
import unittest

from tests.cli import test_rmii_config

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sFixtureDir = os.path.join(os.path.dirname(__file__), 'fixtures', 'vsc8540et_mii_config')
sExampleConstraints = os.path.join(sProjectDir, 'example', 'microchip', 'vsc8540et', 'mii.xdc')
RX_ER_TABLE = '[rx_er]\nport     = "I_MII_RX_ER"\nregister = "q_mii_rx_er_reg"\n'
RX_ER_TRACE = '[[trace]]\nname = "mii_rx_er"\nif_signal = "RX_ER"\npart_to_device = {max_delay = 1.2, min_delay = 0.8}\n'


class MiiConfigTestCase(test_rmii_config.RmiiConfigTestCase):
    '''
    The VSC8540ET example's MII interface as an MII configuration: the FPGA is the MAC, and the PHY sends TX_CLK and
    RX_CLK.  The timing reports are the example's, from Vivado.
    '''

    sFixtureDir = sFixtureDir

    def edit_config(self, sOld, sNew):
        self.edit_file('mii_config.toml', sOld, sNew)

    def generate_interface(self):
        self.assertEqual(0, self.run_stacv(['generate', 'interface', 'mii_config.toml']))
        return self.oStdout.getvalue()


class TestMiiConfig(MiiConfigTestCase):

    def test_check_passes_on_the_timing_reports_of_the_design(self):
        self.assertEqual(0, self.run_stacv(['check', 'mii_config.toml']))
        sOutput = self.oStdout.getvalue()
        self.assertIn('PASSED: O_MII_TXD[3:0].SDR-SS-RT-DO  setup slack 12.790 ns, hold slack 4.561 ns\n', sOutput)
        self.assertIn('PASSED: I_MII_RXD[3:0].SDR-SS-I  setup slack 10.284 ns, hold slack 5.981 ns\n', sOutput)
        self.assertIn('Check Passed', sOutput)

    def test_the_constraints_are_those_of_the_hand_written_interface_file(self):
        # The example's mii.toml was checked against the datasheet and IEEE 802.3 Clause 22; the configuration must
        # time the interface exactly as it does.
        self.assertEqual(0, self.run_stacv(['generate', 'xdc', 'mii_config.toml']))
        with open(sExampleConstraints) as oFile:
            lExpected = test_rmii_config.build_constraint_lines(oFile.read())
        self.assertEqual(lExpected, test_rmii_config.build_constraint_lines(self.oStdout.getvalue()))

    def test_the_mac_launches_on_tx_clk_and_captures_with_rx_clk(self):
        sInterface = self.generate_interface()
        self.assertIn('if_standard = "MII"\nif_role = "MAC"\n', sInterface)
        self.assertIn('[[clock]]\nname = "mii_tx_clk"\nperiod = 40.000\nport = "I_MII_TX_CLK"\nif_signal = "TX_CLK"\n', sInterface)
        self.assertIn('[[clock]]\nname = "mii_rx_clk"\nperiod = 40.000\nport = "I_MII_RX_CLK"\nif_signal = "RX_CLK"\n', sInterface)
        self.assertIn('name = "O_MII_TX_EN"\nmethodology = "SDR-SS-RT-DO"\nif_signal = "TX_EN"\nlaunch_clock = {name = "mii_tx_clk", setup_edge = 0, hold_edge = 0}\ncapture_clock = {name = "mii_tx_clk", setup_edge = 2, hold_edge = 0}\n', sInterface)
        self.assertIn('name = "I_MII_RX_DV"\nmethodology = "SDR-SS-I"\nif_signal = "RX_DV"\nlaunch_clock = {name = "mii_rx_clk", setup_edge = 0, hold_edge = 0}\n', sInterface)

    def test_the_timing_reports_are_named_by_interface_and_signal(self):
        sInterface = self.generate_interface()
        for sSignal in ['TXD', 'TX_EN', 'TX_ER', 'RXD', 'RX_DV', 'RX_ER']:
            self.assertIn(f'    "timing_reports/VSC8540_MII.{sSignal}_timing.rpt",\n', sInterface)

    def test_the_constraints_list_the_clocks(self):
        self.assertEqual(0, self.run_stacv(['generate', 'xdc', 'mii_config.toml']))
        self.assertIn('\n# Clocks:     set in the interface configuration\n#             TX_CLK  mii_tx_clk 40 ns\n#             RX_CLK  mii_rx_clk 40 ns\n', self.oStdout.getvalue())

    def test_an_optional_signal_left_out_is_not_timed(self):
        self.edit_config(RX_ER_TABLE, '')
        self.edit_file('mii_traces.toml', RX_ER_TRACE, '')
        self.assertEqual(0, self.run_stacv(['generate', 'xdc', 'mii_config.toml']))
        self.assertNotIn('RX_ER', self.oStdout.getvalue())


class TestMiiConfigErrors(MiiConfigTestCase):

    def assert_error(self, sIdentifier, sMessage):
        self.assertEqual(2, self.run_stacv(['generate', 'interface', 'mii_config.toml']))
        self.assertEqual(f'ERROR: [{sIdentifier}] mii_config.toml {sMessage}\n', self.oStderr.getvalue())

    def test_a_missing_clock_is_an_error(self):
        self.edit_config('[rx_clk]\nname = "mii_rx_clk"\nport = "I_MII_RX_CLK"\n', '')
        self.assert_error('mii_config_002', 'missing required key "rx_clk"')

    def test_a_misspelled_key_is_an_error(self):
        self.edit_config('[rx_dv]\nport', '[crs_dv]\nport')
        self.assert_error('mii_config_004', 'key "crs_dv" is not a key stacv reads; the keys are interface, name, role, part, traces, timing_reports_dir, tx_clk, rx_clk, txd, tx_en, tx_er, rxd, rx_dv, rx_er')

    def test_a_name_still_to_fill_in_is_an_error(self):
        self.edit_config('port = "I_MII_TX_CLK"', 'port = "FROM_DESIGN_TX_CLK_PORT"')
        self.assert_error('mii_config_006', 'key "port" in [tx_clk] (line 30) is FROM_DESIGN_TX_CLK_PORT; replace it with the name in your design')

    def test_a_bus_port_written_as_its_registers_are_is_an_error(self):
        self.edit_config('port     = "O_MII_TXD[3:0]"', 'port     = "O_MII_TXD[*]"')
        self.assert_error('mii_config_014', 'key "port" in [txd] (line 40) is O_MII_TXD[*]; write a bus port as NAME[upper:lower], such as TXD[1:0], and its register as reg[*]')

    def test_a_phy_is_not_supported_yet(self):
        self.edit_config('role      = "MAC"', 'role      = "PHY"')
        self.assert_error('mii_config_008', 'key "role" (line 18) must be "MAC"; a PHY is not supported yet')

    def test_a_part_without_an_mii_interface_as_the_phy_is_an_error(self):
        self.edit_file('vsc8540et.toml', 'if_standard = "MII"', 'if_standard = "RMII"')
        self.assert_error('mii_config_012', 'key "part" (line 20) names vsc8540et.toml, which has no [[interface]] with if_standard "MII" and if_role "PHY"')
