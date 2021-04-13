
import os
import unittest
import copy

from stacv.timing_report.xilinx import vivado

from tests import utils


sTestDir = os.path.dirname(__file__)
lSetupFile = utils.read_file(os.path.join(sTestDir, 'dac_spi.setup.rpt'))
lHoldFile = utils.read_file(os.path.join(sTestDir, 'dac_spi.hold.rpt'))


class Test(unittest.TestCase):

    def test_parse_output_setup_report(self):
        dExpected = build_output_setup_data_structure()

        self.assertEqual(dExpected, vivado.parse_timing_report(lSetupFile)[0])

    def test_parse_output_hold_report(self):
        dExpected = build_output_hold_data_structure()

        self.assertEqual(dExpected, vivado.parse_timing_report(lHoldFile)[0])

    def test_multiple_reports(self):
        self.maxDiff = None
        dSetupExpected = build_output_setup_data_structure()
        dHoldExpected = build_output_hold_data_structure()

        lInput = copy.deepcopy(lSetupFile)
        lInput.extend(copy.deepcopy(lHoldFile))

        lActual = vivado.parse_timing_report(lInput)

        self.assertEqual(dSetupExpected, lActual[0])
        self.assertEqual(dHoldExpected, lActual[1])
        

def build_output_setup_data_structure():

    dReturn = {}
    dReturn['type'] = 'setup'
    dReturn['launch_edge'] = 40.000
    dReturn['capture_edge'] = 50.000
    dReturn['output_delay'] = 2.000
    dReturn['process_corner'] = 'Fast Process Corner'

    dReturn['data_path'] = []

    dReturn['data_path'].append(build_net_delay_structure(0, 0.000, 'I_CLK'))
    dReturn['data_path'].append(build_cell_delay_structure('K18', 'IBUF', 0.348, 'I_CLK_IBUF_inst/O'))
    dReturn['data_path'].append(build_net_delay_structure(1, 0.685, 'I_CLK_IBUF'))
    dReturn['data_path'].append(build_cell_delay_structure('BUFGCTRL_X0Y0', 'BUFG', 0.029, 'I_CLK_IBUF_BUFG_inst/O'))
    dReturn['data_path'].append(build_net_delay_structure(13, 0.862, 'I_CLK_IBUF_BUFG'))
    dReturn['data_path'].append(build_cell_delay_structure('SLICE_X0Y3', 'FDCE', 0.175, 'q_spi_output_data_reg/Q'))
    dReturn['data_path'].append(build_net_delay_structure(1, 0.600, 'O_DAC_DATA_OBUF'))
    dReturn['data_path'].append(build_cell_delay_structure('U16', 'OBUF', 1.285, 'O_DAC_DATA_OBUF_inst/O'))
    dReturn['data_path'].append(build_net_delay_structure(0, 0.000, 'O_DAC_DATA'))

    dReturn['required_path'] = []

    dReturn['required_path'].append(build_net_delay_structure(0, 0.000, 'I_CLK'))
    dReturn['required_path'].append(build_cell_delay_structure('K18', 'IBUF', 0.160, 'I_CLK_IBUF_inst/O'))
    dReturn['required_path'].append(build_net_delay_structure(1, 0.631, 'I_CLK_IBUF'))
    dReturn['required_path'].append(build_cell_delay_structure('BUFGCTRL_X0Y0', 'BUFG', 0.026, 'I_CLK_IBUF_BUFG_inst/O'))
    dReturn['required_path'].append(build_net_delay_structure(13, 0.591, 'I_CLK_IBUF_BUFG'))
    dReturn['required_path'].append(build_cell_delay_structure('SLICE_X0Y5', 'FDCE', 0.141, 'q_spi_output_clock_reg/Q'))
    dReturn['required_path'].append(build_net_delay_structure(1, 0.316, 'O_DAC_SCLK_OBUF'))
    dReturn['required_path'].append(build_cell_delay_structure('U15', 'OBUF', 1.101, 'O_DAC_SCLK_OBUF_inst/O'))
    dReturn['required_path'].append(build_net_delay_structure(0, 0.000, 'O_DAC_SCLK'))

    return dReturn


def build_output_hold_data_structure():

    dReturn = {}
    dReturn['type'] = 'hold'
    dReturn['launch_edge'] = 0.000
    dReturn['capture_edge'] = 0.000
    dReturn['output_delay'] = 1.000
    dReturn['process_corner'] = 'Fast Process Corner'

    dReturn['data_path'] = []

    dReturn['data_path'].append(build_net_delay_structure(0, 0.000, 'I_CLK'))
    dReturn['data_path'].append(build_cell_delay_structure('K18', 'IBUF', 0.160, 'I_CLK_IBUF_inst/O'))
    dReturn['data_path'].append(build_net_delay_structure(1, 0.631, 'I_CLK_IBUF'))
    dReturn['data_path'].append(build_cell_delay_structure('BUFGCTRL_X0Y0', 'BUFG', 0.026, 'I_CLK_IBUF_BUFG_inst/O'))
    dReturn['data_path'].append(build_net_delay_structure(13, 0.591, 'I_CLK_IBUF_BUFG'))
    dReturn['data_path'].append(build_cell_delay_structure('SLICE_X0Y3', 'FDCE', 0.141, 'q_spi_output_data_reg/Q'))
    dReturn['data_path'].append(build_net_delay_structure(1, 0.339, 'O_DAC_DATA_OBUF'))
    dReturn['data_path'].append(build_cell_delay_structure('U16', 'OBUF', 1.098, 'O_DAC_DATA_OBUF_inst/O'))
    dReturn['data_path'].append(build_net_delay_structure(0, 0.000, 'O_DAC_DATA'))

    dReturn['required_path'] = []

    dReturn['required_path'].append(build_net_delay_structure(0, 0.000, 'I_CLK'))
    dReturn['required_path'].append(build_cell_delay_structure('K18', 'IBUF', 0.348, 'I_CLK_IBUF_inst/O'))
    dReturn['required_path'].append(build_net_delay_structure(1, 0.685, 'I_CLK_IBUF'))
    dReturn['required_path'].append(build_cell_delay_structure('BUFGCTRL_X0Y0', 'BUFG', 0.029, 'I_CLK_IBUF_BUFG_inst/O'))
    dReturn['required_path'].append(build_net_delay_structure(13, 0.862, 'I_CLK_IBUF_BUFG'))
    dReturn['required_path'].append(build_cell_delay_structure('SLICE_X0Y5', 'FDCE', 0.175, 'q_spi_output_clock_reg/Q'))
    dReturn['required_path'].append(build_net_delay_structure(1, 0.572, 'O_DAC_SCLK_OBUF'))
    dReturn['required_path'].append(build_cell_delay_structure('U15', 'OBUF', 1.288, 'O_DAC_SCLK_OBUF_inst/O'))
    dReturn['required_path'].append(build_net_delay_structure(0, 0.000, 'O_DAC_SCLK'))

    return dReturn


def build_net_delay_structure(fan_out, delay, resource):
    dDelay = {}
    dDelay['type'] = 'net'
    dDelay['fan_out'] = fan_out
    dDelay['delay'] = delay
    dDelay['resource'] = resource
    return dDelay


def build_cell_delay_structure(location, delay_type, delay, resource):
    dDelay = {}
    dDelay['type'] = 'cell'
    dDelay['location'] = location
    dDelay['delay_type'] = delay_type
    dDelay['delay'] = delay
    dDelay['resource'] = resource
    return dDelay
