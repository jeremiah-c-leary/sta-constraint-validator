import os
import re
import tempfile
import unittest

from stacv.config import interface_config
from stacv.config import interface_config_error


sValidPort = '''
[[interface.port]]
name = "O_DAC_DATA"
methodology = "SDR-SS-O"
timing_reports = ["O_DAC_DATA_timing.rpt"]
'''


class Test(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sConfigFile = os.path.join(oTemporaryDirectory.name, 'stacv.toml')

    def write_config_file(self, sText):
        with open(self.sConfigFile, 'w') as oFile:
            oFile.write(sText)

    def build_error_pattern(self, sIdentifier, sMessagePattern):
        return r'ERROR: \[' + sIdentifier + r'\] ' + re.escape(self.sConfigFile) + ' ' + sMessagePattern

    def test_read_interface_config_raises_error_if_file_is_not_valid_toml(self):
        self.write_config_file('description = "missing closing quote\n')

        sError = self.build_error_pattern('interface_config_001', r'is not valid TOML: .+ \(at line 1, column \d+\)')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_if_description_is_missing(self):
        self.write_config_file('[[interface]]\nname = "DAC_SPI_1"\n' + sValidPort)

        sError = self.build_error_pattern('interface_config_002', 'missing required key "description"')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_if_no_interface_is_given(self):
        self.write_config_file('description = "No interfaces"\n')

        sError = self.build_error_pattern('interface_config_002', 'missing required key "interface"')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_and_port_if_methodology_is_missing(self):
        lText = []
        lText.append('description = "Port without methodology"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append('[[interface.port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('timing_reports = ["O_DAC_CSF_timing.rpt"]')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_002', 'missing required key "methodology" in interface DAC_SPI_1 port O_DAC_CSF')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)
