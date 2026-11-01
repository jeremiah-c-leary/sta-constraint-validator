import os
import unittest
from unittest import mock

from stacv.interface import interface_config

sTestDir = os.path.dirname(__file__)
sProjectDir = os.path.abspath(os.path.join(sTestDir, '..', '..'))
sInterfaceFile = os.path.join(sTestDir, 'interface_config.toml')


class Test(unittest.TestCase):

    def setUp(self):
        with mock.patch.dict(os.environ, {'PROJ_DIR': sProjectDir}):
            self.oConfig = interface_config.read_interface_config(sInterfaceFile)

    def test_config_keeps_its_description(self):
        self.assertEqual('Two ports on one interface', self.oConfig.description)

    def test_config_keeps_its_interface_name(self):
        self.assertEqual('DAC_SPI_1', self.oConfig.interface_name)

    def test_config_keeps_its_ports_in_order(self):
        lPortNames = []
        for oPort in self.oConfig.ports:
            lPortNames.append(oPort.name)
        self.assertEqual(['O_DAC_DATA', 'O_DAC_CSF'], lPortNames)

    def test_port_keeps_its_methodology(self):
        oPort = self.oConfig.ports[0]

        self.assertEqual('SDR-SS-O', oPort.methodology)

    def test_port_timing_report_paths_have_environment_variables_expanded(self):
        with mock.patch.dict(os.environ, {'PROJ_DIR': sProjectDir}):
            interface_config.resolve_timing_reports(self.oConfig, sInterfaceFile)
        oPort = self.oConfig.ports[1]

        lExpected = []
        lExpected.append(os.path.join(sProjectDir, 'tests', 'timing_report', 'parse', 'vivado', 'dac_spi.setup.rpt'))
        lExpected.append(os.path.join(sProjectDir, 'tests', 'timing_report', 'parse', 'vivado', 'dac_spi.hold.rpt'))
        self.assertEqual(lExpected, oPort.timing_reports)

    def test_part_path_has_environment_variables_expanded(self):
        sExpected = os.path.join(sProjectDir, 'example', 'texas_instruments', 'DAC81404', 'part.toml')
        self.assertEqual(sExpected, self.oConfig.part)

    def test_traces_path_has_environment_variables_expanded(self):
        sExpected = os.path.join(sProjectDir, 'example', 'texas_instruments', 'DAC81404', 'traces.toml')
        self.assertEqual(sExpected, self.oConfig.traces)

    def test_port_keeps_its_launch_clock_setup_edge(self):
        oPort = self.oConfig.ports[0]

        self.assertEqual(8, oPort.launch_clock.setup_edge)

    def test_port_keeps_its_capture_clock_setup_edge(self):
        oPort = self.oConfig.ports[0]

        self.assertEqual('D', oPort.capture_clock.setup_edge)

    def test_each_port_keeps_its_own_setup_edges(self):
        oPort = self.oConfig.ports[1]

        self.assertEqual(6, oPort.launch_clock.setup_edge)
        self.assertEqual('B', oPort.capture_clock.setup_edge)

    def test_port_keeps_its_launch_clock_hold_edge(self):
        oPort = self.oConfig.ports[0]

        self.assertEqual(8, oPort.launch_clock.hold_edge)

    def test_port_keeps_its_capture_clock_hold_edge(self):
        oPort = self.oConfig.ports[0]

        self.assertEqual('B', oPort.capture_clock.hold_edge)

    def test_each_port_keeps_its_own_hold_edges(self):
        oPort = self.oConfig.ports[1]

        self.assertEqual(4, oPort.launch_clock.hold_edge)
        self.assertEqual('B', oPort.capture_clock.hold_edge)

    def test_capture_clock_keeps_its_generator_source(self):
        oPort = self.oConfig.ports[0]

        self.assertEqual('q_spi_output_clock_reg', oPort.capture_clock.generator.source)

    def test_capture_clock_keeps_its_generator_master_pin(self):
        oPort = self.oConfig.ports[0]

        self.assertEqual('C', oPort.capture_clock.generator.master_pin)

    def test_capture_clock_keeps_its_generator_target_pin(self):
        oPort = self.oConfig.ports[0]

        self.assertEqual('Q', oPort.capture_clock.generator.target_pin)

    def test_clock_without_a_generator_has_none(self):
        oPort = self.oConfig.ports[0]

        self.assertIsNone(oPort.launch_clock.generator)

    def test_capture_clock_keeps_its_generator_master_clock(self):
        oPort = self.oConfig.ports[0]

        self.assertEqual('clk_100mhz', oPort.capture_clock.generator.master_clock)

    def test_config_keeps_its_clocks_in_order(self):
        lClockNames = []
        for oClock in self.oConfig.clocks:
            lClockNames.append(oClock.name)
        self.assertEqual(['clk_100mhz', 'dac_sclk'], lClockNames)

    def test_launch_clock_takes_its_period_from_its_clock(self):
        oPort = self.oConfig.ports[0]

        self.assertEqual(10.0, oPort.launch_clock.period)

    def test_capture_clock_takes_its_period_from_its_clock(self):
        oPort = self.oConfig.ports[0]

        self.assertEqual(20, oPort.capture_clock.period)

    def test_capture_clock_takes_its_port_from_its_clock(self):
        oPort = self.oConfig.ports[0]

        self.assertEqual('O_DAC_SCLK', oPort.capture_clock.port)

    def test_ports_share_the_generator_of_their_clock(self):
        oPort = self.oConfig.ports[1]

        self.assertEqual('q_spi_output_clock_reg', oPort.capture_clock.generator.source)

    def test_port_without_a_status_is_analyzed(self):
        oPort = self.oConfig.ports[0]

        self.assertEqual('analyze', oPort.status)

