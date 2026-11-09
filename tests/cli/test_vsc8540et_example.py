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
        self.sPartText = self.sPartText.replace('cko_min = {value = -2.5, symbol = "tSKEWT - RX_CLK delay", source = "Tables 7-25, 5-38"}', 'valid_after = {value = 1.5, symbol = "tHOLD_R", source = "Table 7-27"}', 1)
        self.assertEqual(2, self.run_generate())
        self.assertIn('[part_config_010]', self.oStderr.getvalue())
        self.assertIn('timing in pin RXD[3:0] of interface Compensated RGMII MAC Interface must give cko_max and cko_min, or valid_before and valid_after', self.oStderr.getvalue())

    def test_a_trace_from_a_source_needs_a_delay(self):
        # The shared traces file has no trace from a source since the RMII traces have their own file, so one is added.
        self.sTracesText += '\n[[trace]]\nname = "rmii_clk_to_part"\nsource = "phy_rmii_clkout"\n'
        self.assertEqual(2, self.run_generate())
        self.assertIn('trace rmii_clk_to_part has neither source_to_device nor source_to_part', self.oStderr.getvalue())


class TestNextEdgeDoubleDataRateInput(unittest.TestCase):
    '''
    No example captures on the next edge, so the compensated RGMII receive control is made a DDR-SS-I-NE port.
    '''

    run_generate = TestPartInterfaceSelection.run_generate

    def setUp(self):
        TestPartInterfaceSelection.setUp(self)
        with open(os.path.join(sProjectDir, sExampleDir, 'rgmii_id.toml')) as oFile:
            self.sInterfaceText = oFile.read().replace('$PROJ_DIR', self.sDirectory)
        sSameEdge = 'methodology = "DDR-SS-I-SE"\nlaunch_clock = {name = "rgmii_id_rxc", setup_edge = 2, hold_edge = 2}\ncapture_clock = {name = "rgmii_id_rxc", setup_edge = 2, hold_edge = 1}\nregisters = ["GEN_RGMII_ID_RX[4].U_IDDR"]'
        sNextEdge = 'methodology = "DDR-SS-I-NE"\nlaunch_clock = {name = "rgmii_id_rxc", setup_edge = 0, hold_edge = 0}\ncapture_clock = {name = "rgmii_id_rxc", setup_edge = 1, hold_edge = 0}\nregisters = ["GEN_RGMII_ID_RX[4].U_IDDR"]'
        self.assertIn(sSameEdge, self.sInterfaceText)
        self.sInterfaceText = self.sInterfaceText.replace(sSameEdge, sNextEdge)

    def find_port_constraints(self):
        lConstraints = []
        for sLine in self.oStdout.getvalue().split('\n'):
            if sLine.startswith('set_') and 'I_RGMII_ID_RX_CTL' in sLine:
                lConstraints.append(sLine)
        return lConstraints

    def test_the_edge_pairs_that_do_not_capture_the_data_are_false_paths(self):
        sThrough = '[get_clocks rgmii_id_rxc] -through [get_ports I_RGMII_ID_RX_CTL]'
        lExpected = []
        lExpected.append('set_input_delay -clock [get_clocks rgmii_id_rxc] -max -1.300 [get_ports I_RGMII_ID_RX_CTL]')
        lExpected.append('set_input_delay -clock [get_clocks rgmii_id_rxc] -clock_fall -add_delay -max -1.300 [get_ports I_RGMII_ID_RX_CTL]')
        lExpected.append('set_input_delay -clock [get_clocks rgmii_id_rxc] -min -2.700 [get_ports I_RGMII_ID_RX_CTL]')
        lExpected.append('set_input_delay -clock [get_clocks rgmii_id_rxc] -clock_fall -add_delay -min -2.700 [get_ports I_RGMII_ID_RX_CTL]')
        lExpected.append(f'set_false_path -setup -rise_from {sThrough} -rise_to [get_clocks rgmii_id_rxc]')
        lExpected.append(f'set_false_path -setup -fall_from {sThrough} -fall_to [get_clocks rgmii_id_rxc]')
        lExpected.append(f'set_false_path -hold -rise_from {sThrough} -fall_to [get_clocks rgmii_id_rxc]')
        lExpected.append(f'set_false_path -hold -fall_from {sThrough} -rise_to [get_clocks rgmii_id_rxc]')
        self.assertEqual(0, self.run_generate())
        self.assertEqual(lExpected, self.find_port_constraints())


class TestVsc8540etCheck(ExampleTestCase):
    '''
    Every VSC8540ET interface passes stacv check on the timing reports of the Vivado run in the example.
    '''

    def test_every_port_of_every_interface_passes(self):
        for sInterface in lInterfaces:
            with self.subTest(interface=sInterface):
                iExitCode = self.run_stacv(['check', f'{sExampleDir}/{sInterface}.toml'])
                self.assertEqual('', self.oStderr.getvalue())
                self.assertNotIn('DEFERRED', self.oStdout.getvalue())
                self.assertNotIn('FAILED', self.oStdout.getvalue())
                self.assertTrue(self.oStdout.getvalue().endswith('Check Passed\n'), self.oStdout.getvalue()[-300:])
                self.assertEqual(0, iExitCode)
