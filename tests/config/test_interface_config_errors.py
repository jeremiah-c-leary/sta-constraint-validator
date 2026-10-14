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

    def test_read_interface_config_raises_error_naming_interface_position_if_interface_name_is_missing(self):
        lText = []
        lText.append('description = "Second interface without name"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(sValidPort)
        lText.append('[[interface]]')
        lText.append(sValidPort)
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_002', 'missing required key "name" in interface number 2$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_and_port_position_if_port_name_is_missing(self):
        lText = []
        lText.append('description = "Second port without name"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(sValidPort)
        lText.append('[[interface.port]]')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('timing_reports = ["O_DAC_CSF_timing.rpt"]')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_002', 'missing required key "name" in interface DAC_SPI_1 port number 2$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_if_port_is_missing(self):
        lText = []
        lText.append('description = "Second interface without port"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(sValidPort)
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_2"')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_002', 'missing required key "port" in interface DAC_SPI_2$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_and_port_if_timing_reports_is_missing(self):
        lText = []
        lText.append('description = "Second port without timing reports"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(sValidPort)
        lText.append('[[interface.port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_002', 'missing required key "timing_reports" in interface DAC_SPI_1 port O_DAC_CSF$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_and_port_if_timing_reports_is_a_string(self):
        lText = []
        lText.append('description = "Second port with timing reports as a string"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(sValidPort)
        lText.append('[[interface.port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('timing_reports = "O_DAC_CSF_timing.rpt"')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "timing_reports" in interface DAC_SPI_1 port O_DAC_CSF must be a list of strings$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_and_port_if_timing_reports_contains_a_non_string(self):
        lText = []
        lText.append('description = "Second port with a number in timing reports"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(sValidPort)
        lText.append('[[interface.port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('timing_reports = ["O_DAC_CSF_timing.rpt", 5]')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "timing_reports" in interface DAC_SPI_1 port O_DAC_CSF must be a list of strings$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_position_if_interface_name_is_a_number(self):
        lText = []
        lText.append('description = "Second interface with a number as name"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(sValidPort)
        lText.append('[[interface]]')
        lText.append('name = 7')
        lText.append(sValidPort)
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "name" in interface number 2 must be a string$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_if_description_is_a_number(self):
        self.write_config_file('description = 5\n[[interface]]\nname = "DAC_SPI_1"\n' + sValidPort)

        sError = self.build_error_pattern('interface_config_003', 'key "description" must be a string$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_and_port_position_if_port_name_is_a_number(self):
        lText = []
        lText.append('description = "Second port with a number as name"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(sValidPort)
        lText.append('[[interface.port]]')
        lText.append('name = 7')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('timing_reports = ["O_DAC_CSF_timing.rpt"]')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "name" in interface DAC_SPI_1 port number 2 must be a string$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_and_port_if_methodology_is_a_number(self):
        lText = []
        lText.append('description = "Second port with a number as methodology"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(sValidPort)
        lText.append('[[interface.port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = 3')
        lText.append('timing_reports = ["O_DAC_CSF_timing.rpt"]')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "methodology" in interface DAC_SPI_1 port O_DAC_CSF must be a string$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_if_interface_is_a_string(self):
        self.write_config_file('description = "Interface as a string"\ninterface = "DAC_SPI_1"\n')

        sError = self.build_error_pattern('interface_config_003', 'key "interface" must be an array of tables$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_if_port_is_a_number(self):
        lText = []
        lText.append('description = "Second interface with a number as port"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(sValidPort)
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_2"')
        lText.append('port = 5')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "port" in interface DAC_SPI_2 must be an array of tables$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)
