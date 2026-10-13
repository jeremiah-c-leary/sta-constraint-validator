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

    def test_config_has_one_interface_with_its_name(self):
        lInterfaceNames = []
        for oInterface in self.oConfig.interfaces:
            lInterfaceNames.append(oInterface.name)
        self.assertEqual(['DAC_SPI_1'], lInterfaceNames)

    def test_interface_keeps_its_ports_in_order(self):
        oInterface = self.oConfig.interfaces[0]

        lPortNames = []
        for oPort in oInterface.ports:
            lPortNames.append(oPort.name)
        self.assertEqual(['O_DAC_DATA', 'O_DAC_CSF'], lPortNames)

    def test_port_keeps_its_methodology(self):
        oPort = self.oConfig.interfaces[0].ports[0]

        self.assertEqual('SDR-SS-O', oPort.methodology)

    def test_port_timing_report_paths_have_environment_variables_expanded(self):
        oPort = self.oConfig.interfaces[0].ports[1]

        lExpected = []
        lExpected.append(os.path.join(sProjectDir, 'tests', 'timing_report', 'parse', 'vivado', 'dac_spi.setup.rpt'))
        lExpected.append(os.path.join(sProjectDir, 'tests', 'timing_report', 'parse', 'vivado', 'dac_spi.hold.rpt'))
        self.assertEqual(lExpected, oPort.timing_reports)
