import os
import re
import tempfile
import unittest
from unittest import mock

from stacv.config import interface_config
from stacv.config import interface_config_error


class Test(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        self.sConfigFile = os.path.join(self.sDirectory, 'stacv.toml')
        self.sValidPort = self.build_valid_port()

    def build_valid_port(self):
        sTimingReportFile = os.path.join(self.sDirectory, 'O_DAC_DATA_timing.rpt')
        with open(sTimingReportFile, 'w') as oFile:
            oFile.write('')
        lText = []
        lText.append('[[interface.port]]')
        lText.append('name = "O_DAC_DATA"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append(f'timing_reports = ["{sTimingReportFile}"]')
        return '\n' + '\n'.join(lText) + '\n'

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
        self.write_config_file('[[interface]]\nname = "DAC_SPI_1"\n' + self.sValidPort)

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
        lText.append(self.sValidPort)
        lText.append('[[interface]]')
        lText.append(self.sValidPort)
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_002', 'missing required key "name" in interface number 2$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_and_port_position_if_port_name_is_missing(self):
        lText = []
        lText.append('description = "Second port without name"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(self.sValidPort)
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
        lText.append(self.sValidPort)
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
        lText.append(self.sValidPort)
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
        lText.append(self.sValidPort)
        lText.append('[[interface.port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('timing_reports = "O_DAC_CSF_timing.rpt"')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "timing_reports" in interface DAC_SPI_1 port O_DAC_CSF must be a list of one or more strings$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_and_port_if_timing_reports_contains_a_non_string(self):
        lText = []
        lText.append('description = "Second port with a number in timing reports"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(self.sValidPort)
        lText.append('[[interface.port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('timing_reports = ["O_DAC_CSF_timing.rpt", 5]')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "timing_reports" in interface DAC_SPI_1 port O_DAC_CSF must be a list of one or more strings$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_position_if_interface_name_is_a_number(self):
        lText = []
        lText.append('description = "Second interface with a number as name"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(self.sValidPort)
        lText.append('[[interface]]')
        lText.append('name = 7')
        lText.append(self.sValidPort)
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "name" in interface number 2 must be a non-empty string$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_if_description_is_a_number(self):
        self.write_config_file('description = 5\n[[interface]]\nname = "DAC_SPI_1"\n' + self.sValidPort)

        sError = self.build_error_pattern('interface_config_003', 'key "description" must be a non-empty string$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_and_port_position_if_port_name_is_a_number(self):
        lText = []
        lText.append('description = "Second port with a number as name"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(self.sValidPort)
        lText.append('[[interface.port]]')
        lText.append('name = 7')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('timing_reports = ["O_DAC_CSF_timing.rpt"]')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "name" in interface DAC_SPI_1 port number 2 must be a non-empty string$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_and_port_if_methodology_is_a_number(self):
        lText = []
        lText.append('description = "Second port with a number as methodology"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(self.sValidPort)
        lText.append('[[interface.port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = 3')
        lText.append('timing_reports = ["O_DAC_CSF_timing.rpt"]')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "methodology" in interface DAC_SPI_1 port O_DAC_CSF must be a non-empty string$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_if_interface_is_a_string(self):
        self.write_config_file('description = "Interface as a string"\ninterface = "DAC_SPI_1"\n')

        sError = self.build_error_pattern('interface_config_003', 'key "interface" must be an array of one or more tables$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_if_port_is_a_number(self):
        lText = []
        lText.append('description = "Second interface with a number as port"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(self.sValidPort)
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_2"')
        lText.append('port = 5')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "port" in interface DAC_SPI_2 must be an array of one or more tables$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_if_interface_is_an_empty_list(self):
        self.write_config_file('description = "No interfaces in list"\ninterface = []\n')

        sError = self.build_error_pattern('interface_config_003', 'key "interface" must be an array of one or more tables$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_if_port_is_an_empty_list(self):
        lText = []
        lText.append('description = "Second interface with no ports in list"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(self.sValidPort)
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_2"')
        lText.append('port = []')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "port" in interface DAC_SPI_2 must be an array of one or more tables$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_and_port_if_timing_reports_is_an_empty_list(self):
        lText = []
        lText.append('description = "Second port with no timing reports in list"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(self.sValidPort)
        lText.append('[[interface.port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('timing_reports = []')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "timing_reports" in interface DAC_SPI_1 port O_DAC_CSF must be a list of one or more strings$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_position_if_interface_name_is_empty(self):
        lText = []
        lText.append('description = "Second interface with an empty name"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(self.sValidPort)
        lText.append('[[interface]]')
        lText.append('name = ""')
        lText.append(self.sValidPort)
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "name" in interface number 2 must be a non-empty string$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_port_and_variable_if_environment_variable_is_not_set(self):
        lText = []
        lText.append('description = "Second port uses an unset environment variable"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(self.sValidPort)
        lText.append('[[interface.port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('timing_reports = ["$STACV_UNSET_TEST_VARIABLE/O_DAC_CSF_timing.rpt"]')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_004', 'key "timing_reports" in interface DAC_SPI_1 port O_DAC_CSF uses environment variables that are not set: STACV_UNSET_TEST_VARIABLE$')
        with mock.patch.dict(os.environ):
            os.environ.pop('STACV_UNSET_TEST_VARIABLE', None)
            with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
                interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_all_variables_if_two_environment_variables_are_not_set(self):
        lText = []
        lText.append('description = "Second port uses two unset environment variables"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(self.sValidPort)
        lText.append('[[interface.port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('timing_reports = ["$STACV_UNSET_A/$STACV_UNSET_B/O_DAC_CSF_timing.rpt"]')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_004', 'key "timing_reports" in interface DAC_SPI_1 port O_DAC_CSF uses environment variables that are not set: STACV_UNSET_A, STACV_UNSET_B$')
        with mock.patch.dict(os.environ):
            os.environ.pop('STACV_UNSET_A', None)
            os.environ.pop('STACV_UNSET_B', None)
            with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
                interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_variable_if_braced_environment_variable_is_not_set(self):
        lText = []
        lText.append('description = "Second port uses an unset braced environment variable"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(self.sValidPort)
        lText.append('[[interface.port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('timing_reports = ["${STACV_UNSET_TEST_VARIABLE}/O_DAC_CSF_timing.rpt"]')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_004', 'key "timing_reports" in interface DAC_SPI_1 port O_DAC_CSF uses environment variables that are not set: STACV_UNSET_TEST_VARIABLE$')
        with mock.patch.dict(os.environ):
            os.environ.pop('STACV_UNSET_TEST_VARIABLE', None)
            with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
                interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_interface_port_and_file_if_timing_report_does_not_exist(self):
        sMissingFile = os.path.join(self.sDirectory, 'O_DAC_CSF_timing.rpt')
        lText = []
        lText.append('description = "Second port lists a timing report that does not exist"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(self.sValidPort)
        lText.append('[[interface.port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append(f'timing_reports = ["{sMissingFile}"]')
        self.write_config_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_005', 'key "timing_reports" in interface DAC_SPI_1 port O_DAC_CSF lists a file that does not exist: ' + re.escape(sMissingFile) + '$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sConfigFile)

    def test_read_interface_config_raises_error_naming_expanded_path_if_timing_report_does_not_exist(self):
        lText = []
        lText.append('description = "Second port lists a timing report that does not exist using an environment variable"')
        lText.append('[[interface]]')
        lText.append('name = "DAC_SPI_1"')
        lText.append(self.sValidPort)
        lText.append('[[interface.port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('timing_reports = ["$STACV_TEST_REPORT_DIRECTORY/O_DAC_CSF_timing.rpt"]')
        self.write_config_file('\n'.join(lText) + '\n')

        sMissingFile = os.path.join(self.sDirectory, 'O_DAC_CSF_timing.rpt')
        sError = self.build_error_pattern('interface_config_005', 'key "timing_reports" in interface DAC_SPI_1 port O_DAC_CSF lists a file that does not exist: ' + re.escape(sMissingFile) + '$')
        with mock.patch.dict(os.environ, {'STACV_TEST_REPORT_DIRECTORY': self.sDirectory}):
            with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
                interface_config.read_interface_config(self.sConfigFile)
