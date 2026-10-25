import os
import unittest
from unittest import mock

from stacv.config import interface_config

sTestDir = os.path.dirname(__file__)
sProjectDir = os.path.abspath(os.path.join(sTestDir, '..', '..'))
sConfigFile = os.path.join(sTestDir, 'interface_config.toml')


class Test(unittest.TestCase):

    def setUp(self):
        with mock.patch.dict(os.environ, {'PROJ_DIR': sProjectDir}):
            self.oConfig = interface_config.read_interface_config(sConfigFile)

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

        self.assertEqual('C', oPort.capture_clock.setup_edge)

    def test_each_port_keeps_its_own_setup_edges(self):
        oPort = self.oConfig.ports[1]

        self.assertEqual(6, oPort.launch_clock.setup_edge)
        self.assertEqual('B', oPort.capture_clock.setup_edge)

    def test_port_keeps_its_launch_clock_hold_edge(self):
        oPort = self.oConfig.ports[0]

        self.assertEqual(0, oPort.launch_clock.hold_edge)

    def test_port_keeps_its_capture_clock_hold_edge(self):
        oPort = self.oConfig.ports[0]

        self.assertEqual('A', oPort.capture_clock.hold_edge)

    def test_each_port_keeps_its_own_hold_edges(self):
        oPort = self.oConfig.ports[1]

        self.assertEqual(4, oPort.launch_clock.hold_edge)
        self.assertEqual('B', oPort.capture_clock.hold_edge)
