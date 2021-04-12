
import unittest

from stacv.timing_report import delay_element
from stacv.timing_report import delay_path
from stacv.timing_report import timing_report as tr


class Test(unittest.TestCase):

    def test_new_timing_report(self):

        oDataPath = build_data_path()
        oRequiredPath = build_required_path()

        oTr = tr.new(oDataPath, oRequiredPath)

        oTr.launch_edge = 0.000
        oTr.capture_edge = 0.000
        oTr.output_delay = 1
        oTr.type = 'hold'

        self.assertEqual(0.245, oTr.crpr)
        self.assertEqual(0.246, oTr.get_slack())


def build_data_path():

    oRequiredPath = delay_path.new()

    oRequiredPath.add_delay(create_cell_delay('K18', None, 0, 'I_CLK'))
    oRequiredPath.add_delay(create_net_delay(0, 'I_CLK', 0))

    oRequiredPath.add_delay(create_cell_delay('K18', 'IBUF', 0.160, 'I_CLK'))
    oRequiredPath.add_delay(create_net_delay(0.631, 'I_CLK', 1))

    oRequiredPath.add_delay(create_cell_delay('BUFGCTRL_X0Y0', 'BUFG', 0.026, 'I_CLK_IBUF_BUFG_inst/O'))
    oRequiredPath.add_delay(create_net_delay(0.591, 'I_CLK_IBUF_BUFG', 13))

    oRequiredPath.add_delay(create_cell_delay('SLICE_X1Y4', 'FDCE', 0.141, 'q_spi_output_data_reg/Q'))
    oRequiredPath.add_delay(create_net_delay(0.313, 'O_DAC_DATA_OBUF', 1))

    oRequiredPath.add_delay(create_cell_delay('U16', 'OBUF', 1.098, 'O_DAC_DATA_OBUF_inst/O'))
    oRequiredPath.add_delay(create_net_delay(0, 'O_DAC_DATA', 0))

    return oRequiredPath


def build_required_path():

    oRequiredPath = delay_path.new()

    oRequiredPath.add_delay(create_cell_delay('K18', None, 0, 'I_CLK'))
    oRequiredPath.add_delay(create_net_delay(0, 'I_CLK', 0))

    oRequiredPath.add_delay(create_cell_delay('K18', 'IBUF', 0.348, 'I_CLK'))
    oRequiredPath.add_delay(create_net_delay(0.685, 'I_CLK', 1))

    oRequiredPath.add_delay(create_cell_delay('BUFGCTRL_X0Y0', 'BUFG', 0.029, 'I_CLK_IBUF_BUFG_inst/O'))
    oRequiredPath.add_delay(create_net_delay(0.862, 'I_CLK_IBUF_BUFG', 13))

    oRequiredPath.add_delay(create_cell_delay('SLICE_X0Y0', 'FDCE', 0.175, 'q_spi_clock_reg[4]_lopt_replica/Q'))
    oRequiredPath.add_delay(create_net_delay(0.572, 'q_spi_clock_reg[4]_lopt_replica_1', 1))

    oRequiredPath.add_delay(create_cell_delay('U15', 'OBUF', 1.288, 'O_DAC_SCLK_OBUF_inst/I'))
    oRequiredPath.add_delay(create_net_delay(0, 'O_DAC_SCLK', 0))

    return oRequiredPath


def create_cell_delay(location, delay_type, delay, resource):

    dDelay = {}
    dDelay['type'] = 'cell'
    dDelay['location'] = location
    dDelay['delay_type'] = delay_type
    dDelay['delay'] = delay
    dDelay['resource'] = resource
  
    oDelay = delay_element.new(dDelay)

    return oDelay


def create_net_delay(delay, resource, fan_out):

    dDelay = {}
    dDelay['type'] = 'net'
    dDelay['delay'] = delay
    dDelay['resource'] = resource
    dDelay['fan_out'] = fan_out
  
    oDelay = delay_element.new(dDelay)

    return oDelay
