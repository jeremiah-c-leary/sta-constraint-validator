import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def build_interface_text(lPortNames, sMissingTimingReport, sClockPort):
    lText = []
    lText.append('description = "block diagram test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append('part = "part.toml"')
    lText.append('part_interface = "Serial Interface"')
    lText.append('traces = "traces.toml"')
    lText.append('[[clock]]')
    lText.append('name = "clk_launch"')
    lText.append('period = 10')
    lText.append('[[clock]]')
    lText.append('name = "clk_capture"')
    lText.append('period = 40')
    lText.append(f'port = "{sClockPort}"')
    lText.append('generator = {source = "q_sclk_reg", master_pin = "C", target_pin = "Q", master_clock = "clk_launch"}')
    for sPortName in lPortNames:
        lText.append('')
        lText.append('[[port]]')
        lText.append(f'name = "{sPortName}"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_launch", setup_edge = 4, hold_edge = 4}')
        lText.append('capture_clock = {name = "clk_capture", setup_edge = 2, hold_edge = 0}')
        lText.append(f'registers = ["q_{sPortName.lower()}_reg"]')
        lText.append(f'timing_reports = ["{sMissingTimingReport}"]')
    return '\n'.join(lText) + '\n'


def find_port_names(lTraces, sClockPort):
    # Without an explicit port order, every trace except the clock is a port, in trace order.
    lPortNames = []
    for sTrace in lTraces:
        sDevicePin = sTrace.split('device_pin = "')[1].split('"')[0]
        if sDevicePin != sClockPort:
            lPortNames.append(sDevicePin)
    return lPortNames


def build_part_text(sPartNumber, sPinName='SDIN'):
    lText = []
    lText.append('[properties]')
    lText.append('manufacturer = "Texas Instruments"')
    lText.append(f'part_number = "{sPartNumber}"')
    lText.append('')
    lText.append('[datasheet]')
    lText.append('name = "datasheet"')
    lText.append('url = "https://www.ti.com"')
    lText.append('version = "A"')
    lText.append('')
    lText.append('[[interface]]')
    lText.append('name = "Serial Interface"')
    lText.append('')
    lText.append('[[interface.pin]]')
    lText.append(f'name = "{sPinName}"')
    lText.append('methodology = "SDR-SS-I"')
    lText.append('clock = {pin = "SCLK", max_frequency = 25}')
    lText.append('capture_edge = "Falling"')
    lText.append('setup = {value = 10, symbol = "tSDIS", source = "Table 7.6"}')
    lText.append('hold = {value = 10, symbol = "tSDIH", source = "Table 7.6"}')
    return '\n'.join(lText) + '\n'


def output_trace(sName, sDevicePin, sPartPin):
    return build_trace_text(sName, sDevicePin, sPartPin, 'device_to_part')


def input_trace(sName, sDevicePin, sPartPin):
    return build_trace_text(sName, sDevicePin, sPartPin, 'part_to_device')


def bidirectional_trace(sName, sDevicePin, sPartPin):
    lText = []
    lText.append(output_trace(sName, sDevicePin, sPartPin))
    lText.append('part_to_device = {max_delay = 3.00, min_delay = 1.00}')
    return '\n'.join(lText)


def build_trace_text(sName, sDevicePin, sPartPin, sDirection):
    lText = []
    lText.append('[[trace]]')
    lText.append(f'name = "{sName}"')
    lText.append(f'device_pin = "{sDevicePin}"')
    lText.append(f'part_pin = "{sPartPin}"')
    lText.append(f'{sDirection} = {{max_delay = 3.00, min_delay = 1.00}}')
    return '\n'.join(lText)


def build_dac81404_traces():
    lTraces = []
    lTraces.append(output_trace('data_output', 'O_DAC_DATA', 'SDIN'))
    lTraces.append(output_trace('chip_select', 'O_DAC_CSF', 'CSF'))
    lTraces.append(input_trace('data_input', 'I_DAC_DATA', 'SDO'))
    lTraces.append(bidirectional_trace('data', 'IO_DAC_DATA', 'SDIO'))
    lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
    return lTraces


class BlockDiagramTestCase(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        self.sInterfaceFile = os.path.join(self.sDirectory, 'interface.toml')
        self.sMissingTimingReport = os.path.join(self.sDirectory, 'not_written_yet.rpt')

    def write_file(self, sFilename, sText):
        with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
            oFile.write(sText)

    def run_visualize_block_diagram(self, lTraces, sPartNumber='DAC81404', sClockPort='O_DAC_SCLK', lPortNames=None, sPinName='SDIN'):
        if lPortNames is None:
            lPortNames = find_port_names(lTraces, sClockPort)
        self.write_file('interface.toml', build_interface_text(lPortNames, self.sMissingTimingReport, sClockPort))
        return self.run_with_interface_written(lTraces, sPartNumber, sPinName)

    def run_with_interface_written(self, lTraces, sPartNumber='DAC81404', sPinName='SDIN'):
        self.write_file('part.toml', build_part_text(sPartNumber, sPinName))
        self.write_file('traces.toml', '\n\n'.join(lTraces) + '\n')
        lArgv = ['stacv', 'visualize', 'block_diagram', self.sInterfaceFile]
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', lArgv):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def assert_rows_drawn(self, lExpectedRows):
        self.assertIn('\n'.join(lExpectedRows) + '\n', self.oStdout.getvalue())


class TestVisualizeBlockDiagramDispatch(BlockDiagramTestCase):

    def test_exits_with_zero(self):
        self.assertEqual(0, self.run_visualize_block_diagram(build_dac81404_traces()))

    def test_writes_nothing_to_stderr(self):
        self.run_visualize_block_diagram(build_dac81404_traces())
        self.assertEqual('', self.oStderr.getvalue())


class TestVisualizeBlockDiagramWidths(BlockDiagramTestCase):

    def test_widens_the_device_for_a_longer_port_name(self):
        lTraces = []
        lTraces.append(output_trace('data_output', 'O_DATA_LONGER_NAME', 'SDIN'))
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        self.run_visualize_block_diagram(lTraces)
        lExpected = []
        lExpected.append('-----------------------------------------------------------------------+                       +------------')
        lExpected.append('  Device                                                               |                       |  DAC81404')
        lExpected.append('                                                                       |                       |')
        lExpected.append('  clk_launch --+--> [q_o_data_longer_name_reg] --> O_DATA_LONGER_NAME [X] --- data_output --> [X] SDIN')
        lExpected.append('               |                                                       |                       |')
        lExpected.append('               +--> [q_sclk_reg] ----------------> O_DAC_SCLK         [X] --- clock --------> [X] SCLK')
        lExpected.append('                                                                       |                       |')
        lExpected.append('-----------------------------------------------------------------------+                       +------------')
        self.assert_rows_drawn(lExpected)

    def test_lengthens_every_arrow_for_a_longer_trace_name(self):
        lTraces = []
        lTraces.append(output_trace('serial_data_output', 'O_DAC_DATA', 'SDIN'))
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        self.run_visualize_block_diagram(lTraces)
        lExpected = []
        lExpected.append('-------------------------------------------------------+                              +------------')
        lExpected.append('  Device                                               |                              |  DAC81404')
        lExpected.append('                                                       |                              |')
        lExpected.append('  clk_launch --+--> [q_o_dac_data_reg] --> O_DAC_DATA [X] --- serial_data_output --> [X] SDIN')
        lExpected.append('               |                                       |                              |')
        lExpected.append('               +--> [q_sclk_reg] --------> O_DAC_SCLK [X] --- clock ---------------> [X] SCLK')
        lExpected.append('                                                       |                              |')
        lExpected.append('-------------------------------------------------------+                              +------------')
        self.assert_rows_drawn(lExpected)

    def test_widens_the_part_for_a_longer_part_number(self):
        lTraces = []
        lTraces.append(output_trace('data_output', 'O_DAC_DATA', 'SDIN'))
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        self.run_visualize_block_diagram(lTraces, 'ADC128S102')
        lExpected = []
        lExpected.append('-------------------------------------------------------+                       +--------------')
        lExpected.append('  Device                                               |                       |  ADC128S102')
        lExpected.append('                                                       |                       |')
        lExpected.append('  clk_launch --+--> [q_o_dac_data_reg] --> O_DAC_DATA [X] --- data_output --> [X] SDIN')
        lExpected.append('               |                                       |                       |')
        lExpected.append('               +--> [q_sclk_reg] --------> O_DAC_SCLK [X] --- clock --------> [X] SCLK')
        lExpected.append('                                                       |                       |')
        lExpected.append('-------------------------------------------------------+                       +--------------')
        self.assert_rows_drawn(lExpected)

    def test_widens_the_part_for_a_pin_name_longer_than_the_part_number(self):
        lTraces = []
        lTraces.append(output_trace('data_output', 'O_DAC_DATA', 'SDIN_LONG_NAME'))
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        self.run_visualize_block_diagram(lTraces, 'DAC1', sPinName='SDIN_LONG_NAME')
        lExpected = []
        lExpected.append('-------------------------------------------------------+                       +------------------')
        lExpected.append('  Device                                               |                       |  DAC1')
        lExpected.append('                                                       |                       |')
        lExpected.append('  clk_launch --+--> [q_o_dac_data_reg] --> O_DAC_DATA [X] --- data_output --> [X] SDIN_LONG_NAME')
        lExpected.append('               |                                       |                       |')
        lExpected.append('               +--> [q_sclk_reg] --------> O_DAC_SCLK [X] --- clock --------> [X] SCLK')
        lExpected.append('                                                       |                       |')
        lExpected.append('-------------------------------------------------------+                       +------------------')
        self.assert_rows_drawn(lExpected)

    def test_keeps_the_device_wide_enough_for_its_label(self):
        # With no register to draw, the port names start at the indent, as the device's label does.
        self.write_file('interface.toml', build_interface_text([], self.sMissingTimingReport, 'C') + '\n[[port]]\nname = "D"\nstatus = "defer"\n')
        self.run_with_interface_written([output_trace('d', 'D', 'SDIN'), output_trace('c', 'C', 'SCLK')])
        lExpected = []
        lExpected.append('----------+             +------------')
        lExpected.append('  Device  |             |  DAC81404')
        lExpected.append('          |             |')
        lExpected.append('  D      [X] --- d --> [X] SDIN')
        lExpected.append('          |             |')
        lExpected.append('----------+             +------------')
        self.assert_rows_drawn(lExpected)


class TestVisualizeBlockDiagramRowOrder(BlockDiagramTestCase):

    def assert_trace_rows_in_order(self, lExpectedPorts):
        # Each row with a trace, by the port it names.
        lPorts = []
        for sLine in self.oStdout.getvalue().split('\n'):
            if '[X]' in sLine:
                lPorts.append(sLine.split('[X]')[0].split()[-1])
        self.assertEqual(lExpectedPorts, lPorts)

    def test_draws_rows_in_the_order_of_the_interface_ports(self):
        lPortNames = ['I_DAC_DATA', 'O_DAC_DATA', 'O_DAC_CSF']
        self.run_visualize_block_diagram(build_dac81404_traces(), lPortNames=lPortNames)
        self.assert_trace_rows_in_order(['I_DAC_DATA', 'O_DAC_DATA', 'O_DAC_CSF', 'O_DAC_SCLK'])

    def test_draws_the_clock_last_when_it_comes_first_in_the_traces(self):
        lTraces = []
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        lTraces.append(output_trace('data_output', 'O_DAC_DATA', 'SDIN'))
        self.run_visualize_block_diagram(lTraces)
        self.assert_trace_rows_in_order(['O_DAC_DATA', 'O_DAC_SCLK'])

    def test_leaves_out_a_trace_that_no_port_names(self):
        lTraces = []
        lTraces.append(output_trace('data_output', 'O_DAC_DATA', 'SDIN'))
        lTraces.append(output_trace('chip_select_with_a_long_name', 'O_DAC_CSF', 'CSF'))
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        self.run_visualize_block_diagram(lTraces, lPortNames=['O_DAC_DATA'])
        self.assert_trace_rows_in_order(['O_DAC_DATA', 'O_DAC_SCLK'])

    def test_draws_a_forwarded_clock_without_a_generator_after_the_trees(self):
        # Without a generator there is no element to draw, so the clock's port stands alone, as a deferred port does.
        sInterface = build_interface_text(['O_DAC_DATA'], self.sMissingTimingReport, 'O_DAC_SCLK')
        sInterface = sInterface.replace('generator = {source = "q_sclk_reg", master_pin = "C", target_pin = "Q", master_clock = "clk_launch"}\n', '')
        self.write_file('interface.toml', sInterface)
        self.run_with_interface_written([output_trace('clock', 'O_DAC_SCLK', 'SCLK'), output_trace('data_output', 'O_DAC_DATA', 'SDIN')])
        self.assert_rows_drawn(['  clk_launch --+--> [q_o_dac_data_reg] --> O_DAC_DATA [X] --- data_output --> [X] SDIN'])
        self.assert_trace_rows_in_order(['O_DAC_DATA', 'O_DAC_SCLK'])


class TestVisualizeBlockDiagramDirections(BlockDiagramTestCase):

    def test_draws_both_arrow_heads_for_a_trace_in_both_directions(self):
        lTraces = []
        lTraces.append(output_trace('data_output', 'O_DAC_DATA', 'SDIN'))
        lTraces.append(bidirectional_trace('data', 'IO_DAC_DATA', 'SDIO'))
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        self.run_visualize_block_diagram(lTraces)
        self.assertIn('[X] <-- data ---------> [X] SDIO', self.oStdout.getvalue())


class TestVisualizeBlockDiagramErrors(BlockDiagramTestCase):

    def test_reports_a_traces_error(self):
        lTraces = []
        lTraces.append(output_trace('data_output', 'O_DAC_DATA', 'SDIN').replace('{max_delay = 3.00, min_delay = 1.00}', '{}'))
        lTraces.append(output_trace('clock', 'O_DAC_SCLK', 'SCLK'))
        self.assertEqual(2, self.run_visualize_block_diagram(lTraces))
        self.assertRegex(self.oStderr.getvalue(), r'^ERROR: \[traces_config_005\] ')


class TestVisualizeBlockDiagramDeferredPorts(BlockDiagramTestCase):

    def test_draws_a_deferred_port_after_the_trees(self):
        # A deferred port lists no registers, so it is drawn on its own, after the trees.
        self.write_file('interface.toml', build_interface_text(['O_DAC_DATA'], self.sMissingTimingReport, 'O_DAC_SCLK') + '\n[[port]]\nname = "O_DAC_CSF"\nstatus = "defer"\n')
        self.assertEqual(0, self.run_with_interface_written(build_dac81404_traces()))
        lExpected = []
        lExpected.append('-------------------------------------------------------+                       +------------')
        lExpected.append('  Device                                               |                       |  DAC81404')
        lExpected.append('                                                       |                       |')
        lExpected.append('  clk_launch --+--> [q_o_dac_data_reg] --> O_DAC_DATA [X] --- data_output --> [X] SDIN')
        lExpected.append('               |                                       |                       |')
        lExpected.append('               +--> [q_sclk_reg] --------> O_DAC_SCLK [X] --- clock --------> [X] SCLK')
        lExpected.append('                                                       |                       |')
        lExpected.append('                                           O_DAC_CSF  [X] --- chip_select --> [X] CSF')
        lExpected.append('                                                       |                       |')
        lExpected.append('-------------------------------------------------------+                       +------------')
        self.assert_rows_drawn(lExpected)


class TestVisualizeBlockDiagramExamples(unittest.TestCase):
    '''
    The examples' block diagrams, run from the project directory as a user would.
    '''

    def setUp(self):
        sWorkingDir = os.getcwd()
        self.addCleanup(os.chdir, sWorkingDir)
        os.chdir(sProjectDir)

    def draw(self, sInterfaceFile):
        oStdout = io.StringIO()
        with mock.patch('sys.argv', ['stacv', 'visualize', 'block_diagram', sInterfaceFile]):
            with contextlib.redirect_stdout(oStdout):
                with self.assertRaises(SystemExit) as oContext:
                    __main__.main()
        self.assertEqual(0, oContext.exception.code)
        return oStdout.getvalue().rstrip('\n').split('\n')

    def test_draws_the_dac81404_example(self):
        # Each register, clocked by clk_100mhz, drives or captures its port; the clock register forwards O_DAC_SCLK.
        lExpected = []
        lExpected.append('---------------------------------------------------------------+                       +------------')
        lExpected.append('  Device                                                       |                       |  DAC81404')
        lExpected.append('                                                               |                       |')
        lExpected.append('  clk_100mhz --+--> [q_spi_output_data_reg] ---> O_DAC_DATA   [X] --- data_output --> [X] SDIN')
        lExpected.append('               |                                               |                       |')
        lExpected.append('               +--> [q_spi_sden_f_reg] --------> O_DAC_SDEN_F [X] --- chip_select --> [X] CSF')
        lExpected.append('               |                                               |                       |')
        lExpected.append('               +--> [q_spi_input_data_reg] <---- I_DAC_DATA   [X] <-- data_input ---- [X] SDO')
        lExpected.append('               |                                               |                       |')
        lExpected.append('               +--> [q_spi_output_clock_reg] --> O_DAC_SCLK   [X] --- clock --------> [X] SCLK')
        lExpected.append('                                                               |                       |')
        lExpected.append('---------------------------------------------------------------+                       +------------')
        self.assertEqual(lExpected, self.draw('example/texas_instruments/DAC81404/interface.toml'))

    def test_joins_the_registers_of_a_bidirectional_port(self):
        # IO_MDIO has two tables: q_mdio_out_reg and q_mdio_oe_reg drive it, q_mdio_in_reg captures it.
        lExpected = []
        lExpected.append('------------------------------------------------------+                +-------------')
        lExpected.append('  Device                                              |                |  VSC8540ET')
        lExpected.append('                                                      |                |')
        lExpected.append('  clk_100mhz --+--> [q_mdio_out_reg] --+--> IO_MDIO  [X] <-- mdio --> [X] MDIO')
        lExpected.append('               |                       |              |                |')
        lExpected.append('               +--> [q_mdio_oe_reg] ---+              |                |')
        lExpected.append('               |                       |              |                |')
        lExpected.append('               +--> [q_mdio_in_reg] <--+              |                |')
        lExpected.append('               |                                      |                |')
        lExpected.append('               +--> [q_mdc_reg] -----------> O_MDC   [X] --- mdc ---> [X] MDC')
        lExpected.append('                                                      |                |')
        lExpected.append('------------------------------------------------------+                +-------------')
        self.assertEqual(lExpected, self.draw('example/microchip/vsc8540et/mdio.toml'))

    def test_roots_a_tree_on_the_port_a_clock_enters_on(self):
        # The PHY sends both clocks, so each tree hangs from the port its clock enters on.
        lExpected = []
        lExpected.append('-----------------------------------------------------------+                      +-------------')
        lExpected.append('  Device                                                   |                      |  VSC8540ET')
        lExpected.append('                                                           |                      |')
        lExpected.append('  mii_tx_clk <-+-------------------------- I_MII_TX_CLK   [X] <-- mii_tx_clk --- [X] MII_TXCLK')
        lExpected.append('               |                                           |                      |')
        lExpected.append('               +--> [q_mii_txd_reg[*]] --> O_MII_TXD[3:0] [X] --- mii_txd -----> [X] TXD[3:0]')
        lExpected.append('               |                                           |                      |')
        lExpected.append('               +--> [q_mii_tx_en_reg] ---> O_MII_TX_EN    [X] --- mii_tx_en ---> [X] TX_EN')
        lExpected.append('               |                                           |                      |')
        lExpected.append('               +--> [q_mii_tx_er_reg] ---> O_MII_TX_ER    [X] --- mii_tx_er ---> [X] TX_ER')
        lExpected.append('                                                           |                      |')
        lExpected.append('  mii_rx_clk <-+-------------------------- I_MII_RX_CLK   [X] <-- mii_rx_clk --- [X] RX_CLK')
        lExpected.append('               |                                           |                      |')
        lExpected.append('               +--> [q_mii_rxd_reg[*]] <-- I_MII_RXD[3:0] [X] <-- mii_rxd ------ [X] RXD[3:0]')
        lExpected.append('               |                                           |                      |')
        lExpected.append('               +--> [q_mii_rx_dv_reg] <--- I_MII_RX_DV    [X] <-- mii_rx_dv ---- [X] RX_DV')
        lExpected.append('               |                                           |                      |')
        lExpected.append('               +--> [q_mii_rx_er_reg] <--- I_MII_RX_ER    [X] <-- mii_rx_er ---- [X] RX_ER')
        lExpected.append('                                                           |                      |')
        lExpected.append('-----------------------------------------------------------+                      +-------------')
        self.assertEqual(lExpected, self.draw('example/microchip/vsc8540et/mii.toml'))

    def test_brings_a_clock_from_a_source_in_from_the_top_edge(self):
        # The source drives the device and the part; its name and its drop sit between the boxes.
        lExpected = []
        lExpected.append('---------------------------------------------------------------+                    (phy_rmii_clkout)                  +---------------------')
        lExpected.append('  Device                                                       |                            v                          |  VSC8540ET')
        lExpected.append('                                                               |                            |                          |')
        lExpected.append('  rmii_ref_clk <-+--------------------------- I_RMII_REF_CLK  [X] <-- rmii_clk_to_device ---+--- rmii_clk_to_part --> [X] RMII_CLKIN')
        lExpected.append('                 |                                             |                                                       |')
        lExpected.append('                 +--> [q_rmii_txd_reg[*]] --> O_RMII_TXD[1:0] [X] --- rmii_txd -------------------------------------> [X] TXD[1:0]')
        lExpected.append('                 |                                             |                                                       |')
        lExpected.append('                 +--> [q_rmii_tx_en_reg] ---> O_RMII_TX_EN    [X] --- rmii_tx_en -----------------------------------> [X] TX_EN')
        lExpected.append('                 |                                             |                                                       |')
        lExpected.append('                 +--> [q_rmii_tx_er_reg] ---> O_RMII_TX_ER    [X] --- rmii_tx_er -----------------------------------> [X] TX_ER')
        lExpected.append('                 |                                             |                                                       |')
        lExpected.append('                 +--> [q_rmii_rxd_reg[*]] <-- I_RMII_RXD[1:0] [X] <-- rmii_rxd -------------------------------------- [X] RXD[1:0]')
        lExpected.append('                 |                                             |                                                       |')
        lExpected.append('                 +--> [q_rmii_crs_dv_reg] <-- I_RMII_CRS_DV   [X] <-- rmii_crs_dv ----------------------------------- [X] CRS_DV')
        lExpected.append('                 |                                             |                                                       |')
        lExpected.append('                 +--> [q_rmii_rx_er_reg] <--- I_RMII_RX_ER    [X] <-- rmii_rx_er ------------------------------------ [X] RX_ER')
        lExpected.append('                                                               |                                                       |')
        lExpected.append('---------------------------------------------------------------+                                                       +---------------------')
        self.assertEqual(lExpected, self.draw('example/microchip/vsc8540et/rmii.toml'))
