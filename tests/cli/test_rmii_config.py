import contextlib
import io
import os
import shutil
import tempfile
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sFixtureDir = os.path.join(os.path.dirname(__file__), 'fixtures', 'vsc8540et_rmii_config')
sExampleConstraints = os.path.join(sProjectDir, 'example', 'microchip', 'vsc8540et', 'rmii.xdc')
RX_ER_TABLE = '[rx_er]\nport     = "I_RMII_RX_ER"\nregister = "q_rmii_rx_er_reg"\n'
RX_ER_TRACE = '[[trace]]\nname = "rmii_rx_er"\nif_signal = "RX_ER"\npart_to_device = {max_delay = 1.2, min_delay = 0.8}\n'


class RmiiConfigTestCase(unittest.TestCase):
    '''
    The VSC8540ET example's RMII interface as an RMII configuration: the FPGA is the MAC, and the PHY drives the 50 MHz
    REF_CLK to both ends.  The timing reports are the example's, from Vivado.
    '''

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = os.path.join(oTemporaryDirectory.name, 'vsc8540et')
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
        self.edit_file('rmii_config.toml', sOld, sNew)

    def generate_interface(self):
        self.assertEqual(0, self.run_stacv(['generate', 'interface', 'rmii_config.toml']))
        return self.oStdout.getvalue()


class TestRmiiConfig(RmiiConfigTestCase):

    def test_check_passes_on_the_timing_reports_of_the_design(self):
        self.assertEqual(0, self.run_stacv(['check', 'rmii_config.toml']))
        sOutput = self.oStdout.getvalue()
        self.assertIn('PASSED: O_RMII_TXD[1:0].SDR-SYS-O  setup slack 4.102 ns, hold slack 2.246 ns\n', sOutput)
        self.assertIn('PASSED: I_RMII_RXD[1:0].SDR-SYS-I  setup slack 3.208 ns, hold slack 0.036 ns\n', sOutput)
        self.assertIn('Check Passed', sOutput)

    def test_the_constraints_are_those_of_the_hand_written_interface_file(self):
        # The example's rmii.toml was checked against the datasheet and the RMII specification; the configuration must
        # time the interface exactly as it does.
        self.assertEqual(0, self.run_stacv(['generate', 'xdc', 'rmii_config.toml']))
        with open(sExampleConstraints) as oFile:
            lExpected = build_constraint_lines(oFile.read())
        self.assertEqual(lExpected, build_constraint_lines(self.oStdout.getvalue()))

    def test_the_interface_receives_ref_clk_and_times_each_signal_on_its_rising_edges(self):
        sInterface = self.generate_interface()
        self.assertIn('if_standard = "RMII"\nif_role = "MAC"\n', sInterface)
        self.assertIn('[[clock]]\nname = "rmii_ref_clk"\nperiod = 20.000\nport = "I_RMII_REF_CLK"\nif_signal = "REF_CLK"\n', sInterface)
        self.assertIn('name = "O_RMII_TX_EN"\nmethodology = "SDR-SYS-O"\nif_signal = "TX_EN"\nlaunch_clock = {name = "rmii_ref_clk", setup_edge = 0, hold_edge = 0}\ncapture_clock = {name = "rmii_ref_clk", setup_edge = 2, hold_edge = 0}\n', sInterface)
        self.assertIn('name = "I_RMII_CRS_DV"\nmethodology = "SDR-SYS-I"\nif_signal = "CRS_DV"\n', sInterface)

    def test_the_timing_reports_are_named_by_interface_and_signal(self):
        sInterface = self.generate_interface()
        for sSignal in ['TXD', 'TX_EN', 'TX_ER', 'RXD', 'CRS_DV', 'RX_ER']:
            self.assertIn(f'    "timing_reports/VSC8540_RMII.{sSignal}_timing.rpt",\n', sInterface)

    def test_the_constraints_list_the_clock(self):
        self.assertEqual(0, self.run_stacv(['generate', 'xdc', 'rmii_config.toml']))
        self.assertIn('\n# Clocks:     set in the interface configuration\n#             REF_CLK  rmii_ref_clk 20 ns\n', self.oStdout.getvalue())

    def test_an_optional_signal_left_out_is_not_timed(self):
        self.edit_config(RX_ER_TABLE, '')
        self.edit_file('rmii_traces.toml', RX_ER_TRACE, '')
        self.assertEqual(0, self.run_stacv(['generate', 'xdc', 'rmii_config.toml']))
        self.assertNotIn('RX_ER', self.oStdout.getvalue())


class TestRmiiConfigErrors(RmiiConfigTestCase):

    def assert_error(self, sIdentifier, sMessage):
        self.assertEqual(2, self.run_stacv(['generate', 'interface', 'rmii_config.toml']))
        self.assertEqual(f'ERROR: [{sIdentifier}] rmii_config.toml {sMessage}\n', self.oStderr.getvalue())

    def test_a_missing_key_is_reported_at_its_table(self):
        self.edit_config('register = "q_rmii_tx_en_reg"\n', '')
        self.assert_error('rmii_config_002', 'missing required key "register" in [tx_en] (line 34)')

    def test_a_missing_required_signal_is_an_error(self):
        self.edit_config('[crs_dv]\nport     = "I_RMII_CRS_DV"\nregister = "q_rmii_crs_dv_reg"\n', '')
        self.assert_error('rmii_config_002', 'missing required key "crs_dv"')

    def test_a_misspelled_key_is_an_error(self):
        self.edit_config('[tx_er]\nport', '[tx_err]\nport')
        self.assert_error('rmii_config_004', 'key "tx_err" is not a key stacv reads; the keys are interface, name, role, part, traces, timing_reports_dir, ref_clk, txd, tx_en, tx_er, rxd, crs_dv, rx_er')

    def test_a_name_still_to_fill_in_is_an_error(self):
        self.edit_config('port = "I_RMII_REF_CLK"', 'port = "FROM_DESIGN_REF_CLK_PORT"')
        self.assert_error('rmii_config_006', 'key "port" in [ref_clk] (line 26) is FROM_DESIGN_REF_CLK_PORT; replace it with the name in your design')

    def test_a_phy_is_not_supported_yet(self):
        self.edit_config('role      = "MAC"', 'role      = "PHY"')
        self.assert_error('rmii_config_008', 'key "role" (line 15) must be "MAC"; a PHY is not supported yet')

    def test_a_part_without_an_rmii_interface_as_the_phy_is_an_error(self):
        self.edit_file('vsc8540et.toml', 'if_standard = "RMII"', 'if_standard = "SPI mode 0"')
        self.assert_error('rmii_config_012', 'key "part" (line 17) names vsc8540et.toml, which has no [[interface]] with if_standard "RMII" and if_role "PHY"')


def build_constraint_lines(sConstraints):
    # The constraints, without the comments that name the files they were generated from.
    lLines = []
    for sLine in sConstraints.split('\n'):
        if sLine.startswith('#') or sLine.strip() == '':
            continue
        lLines.append(sLine)
    return lLines
