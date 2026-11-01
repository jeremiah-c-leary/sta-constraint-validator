import os
import pathlib
import re
import tempfile
import unittest
from unittest import mock

from stacv.interface import interface_config
from stacv.interface import interface_config_error


CLOCK_TABLES = '''
[[clock]]
name = "clk_100mhz"
period = 10.000

[[clock]]
name = "dac_sclk"
period = 20
port = "O_DAC_SCLK"
'''


class Test(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        self.sInterfaceFile = os.path.join(self.sDirectory, 'interface.toml')
        self.sValidPort = self.build_valid_port()
        self.write_empty_file('part.toml')
        self.write_empty_file('traces.toml')

    def write_empty_file(self, sFilename):
        with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
            oFile.write('')

    def build_valid_port(self):
        sTimingReportFile = os.path.join(self.sDirectory, 'O_DAC_DATA_timing.rpt')
        with open(sTimingReportFile, 'w') as oFile:
            oFile.write('')
        lText = []
        lText.append('[[port]]')
        lText.append('name = "O_DAC_DATA"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lText.append(f'timing_reports = ["{sTimingReportFile}"]')
        return '\n' + '\n'.join(lText) + '\n'

    def build_port(self, sName, sMethodology):
        sTimingReportFile = os.path.join(self.sDirectory, 'O_DAC_DATA_timing.rpt')
        lText = []
        lText.append('[[port]]')
        lText.append(f'name = "{sName}"')
        lText.append(f'methodology = "{sMethodology}"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lText.append(f'timing_reports = ["{sTimingReportFile}"]')
        return '\n' + '\n'.join(lText) + '\n'

    def write_interface_file(self, sText):
        # Every port in these tests uses the same two clocks, so they are defined once at the end of the file.
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(sText + '\n' + CLOCK_TABLES)

    def build_error_pattern(self, sIdentifier, sMessagePattern):
        return r'ERROR: \[' + sIdentifier + r'\] ' + re.escape(self.sInterfaceFile) + ' ' + sMessagePattern

    def test_read_interface_config_raises_error_if_file_is_not_valid_toml(self):
        self.write_interface_file('description = "missing closing quote\n')

        sError = self.build_error_pattern('interface_config_001', r'is not valid TOML: .+ \(at line 1, column \d+\)')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_if_description_is_missing(self):
        self.write_interface_file('name = "DAC_SPI_1"\n' + self.sValidPort)

        sError = self.build_error_pattern('interface_config_002', 'missing required key "description"$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_if_interface_name_is_missing(self):
        self.write_interface_file('description = "No interface name"' + self.sValidPort)

        sError = self.build_error_pattern('interface_config_002', 'missing required key "name"$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_if_port_is_missing(self):
        self.write_interface_file('description = "No ports"\nname = "DAC_SPI_1"\npart = "part.toml"\ntraces = "traces.toml"\n')

        sError = self.build_error_pattern('interface_config_002', 'missing required key "port"$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_port_if_methodology_is_missing(self):
        lText = []
        lText.append('description = "Port without methodology"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append('[[port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('timing_reports = ["O_DAC_CSF_timing.rpt"]')
        self.write_interface_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_002', 'missing required key "methodology" in port O_DAC_CSF$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_port_position_if_port_name_is_missing(self):
        lText = []
        lText.append('description = "Second port without name"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append(self.sValidPort)
        lText.append('[[port]]')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lText.append('timing_reports = ["O_DAC_CSF_timing.rpt"]')
        self.write_interface_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_002', 'missing required key "name" in port number 2$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_port_if_timing_reports_is_missing(self):
        lText = []
        lText.append('description = "Second port without timing reports"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append(self.sValidPort)
        lText.append('[[port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        self.write_interface_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_002', 'missing required key "timing_reports" in port O_DAC_CSF$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_port_if_timing_reports_is_a_string(self):
        lText = []
        lText.append('description = "Second port with timing reports as a string"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append(self.sValidPort)
        lText.append('[[port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lText.append('timing_reports = "O_DAC_CSF_timing.rpt"')
        self.write_interface_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "timing_reports" in port O_DAC_CSF must be a list of one or more strings$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_port_if_timing_reports_contains_a_non_string(self):
        lText = []
        lText.append('description = "Second port with a number in timing reports"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append(self.sValidPort)
        lText.append('[[port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lText.append('timing_reports = ["O_DAC_CSF_timing.rpt", 5]')
        self.write_interface_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "timing_reports" in port O_DAC_CSF must be a list of one or more strings$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_if_description_is_a_number(self):
        self.write_interface_file('description = 5\nname = "DAC_SPI_1"\n' + self.sValidPort)

        sError = self.build_error_pattern('interface_config_003', 'key "description" must be a non-empty string$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_if_interface_name_is_a_number(self):
        self.write_interface_file('description = "Interface name is a number"\nname = 7\n' + self.sValidPort)

        sError = self.build_error_pattern('interface_config_003', 'key "name" must be a non-empty string$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_if_interface_name_is_empty(self):
        self.write_interface_file('description = "Interface name is empty"\nname = ""\n' + self.sValidPort)

        sError = self.build_error_pattern('interface_config_003', 'key "name" must be a non-empty string$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_if_only_the_old_interface_key_names_the_interface(self):
        lText = []
        lText.append('description = "Configuration written with the old interface key"')
        lText.append('interface = "DAC_SPI_1"')
        lText.append(self.sValidPort)
        self.write_interface_file('\n'.join(lText) + '\n')

        # The old key is reported as unknown before the missing name, which tells the user more.
        sError = self.build_error_pattern('interface_config_004', 'key "interface" is not a key stacv reads; the keys are description, name, part, traces, clock, port$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_port_position_if_port_name_is_a_number(self):
        lText = []
        lText.append('description = "Second port with a number as name"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append(self.sValidPort)
        lText.append('[[port]]')
        lText.append('name = 7')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lText.append('timing_reports = ["O_DAC_CSF_timing.rpt"]')
        self.write_interface_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "name" in port number 2 must be a non-empty string$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_port_if_methodology_is_a_number(self):
        lText = []
        lText.append('description = "Second port with a number as methodology"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append(self.sValidPort)
        lText.append('[[port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = 3')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lText.append('timing_reports = ["O_DAC_CSF_timing.rpt"]')
        self.write_interface_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "methodology" in port O_DAC_CSF must be a non-empty string$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_if_port_is_a_number(self):
        self.write_interface_file('description = "Port is a number"\nname = "DAC_SPI_1"\npart = "part.toml"\ntraces = "traces.toml"\nport = 5\n')

        sError = self.build_error_pattern('interface_config_003', 'key "port" must be an array of one or more tables$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_if_port_is_an_empty_list(self):
        self.write_interface_file('description = "No ports in list"\nname = "DAC_SPI_1"\npart = "part.toml"\ntraces = "traces.toml"\nport = []\n')

        sError = self.build_error_pattern('interface_config_003', 'key "port" must be an array of one or more tables$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_port_if_timing_reports_is_an_empty_list(self):
        lText = []
        lText.append('description = "Second port with no timing reports in list"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append(self.sValidPort)
        lText.append('[[port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lText.append('timing_reports = []')
        self.write_interface_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_003', 'key "timing_reports" in port O_DAC_CSF must be a list of one or more strings$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_port_and_variable_if_environment_variable_is_not_set(self):
        lText = []
        lText.append('description = "Second port uses an unset environment variable"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append(self.sValidPort)
        lText.append('[[port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lText.append('timing_reports = ["$STACV_UNSET_TEST_VARIABLE/O_DAC_CSF_timing.rpt"]')
        self.write_interface_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_005', 'key "timing_reports" in port O_DAC_CSF uses environment variables that are not set: STACV_UNSET_TEST_VARIABLE$')
        with mock.patch.dict(os.environ):
            os.environ.pop('STACV_UNSET_TEST_VARIABLE', None)
            oInterface = interface_config.read_interface_config(self.sInterfaceFile)
            with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
                interface_config.resolve_timing_reports(oInterface, self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_all_variables_if_two_environment_variables_are_not_set(self):
        lText = []
        lText.append('description = "Second port uses two unset environment variables"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append(self.sValidPort)
        lText.append('[[port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lText.append('timing_reports = ["$STACV_UNSET_A/$STACV_UNSET_B/O_DAC_CSF_timing.rpt"]')
        self.write_interface_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_005', 'key "timing_reports" in port O_DAC_CSF uses environment variables that are not set: STACV_UNSET_A, STACV_UNSET_B$')
        with mock.patch.dict(os.environ):
            os.environ.pop('STACV_UNSET_A', None)
            os.environ.pop('STACV_UNSET_B', None)
            oInterface = interface_config.read_interface_config(self.sInterfaceFile)
            with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
                interface_config.resolve_timing_reports(oInterface, self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_variable_if_braced_environment_variable_is_not_set(self):
        lText = []
        lText.append('description = "Second port uses an unset braced environment variable"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append(self.sValidPort)
        lText.append('[[port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lText.append('timing_reports = ["${STACV_UNSET_TEST_VARIABLE}/O_DAC_CSF_timing.rpt"]')
        self.write_interface_file('\n'.join(lText) + '\n')

        sError = self.build_error_pattern('interface_config_005', 'key "timing_reports" in port O_DAC_CSF uses environment variables that are not set: STACV_UNSET_TEST_VARIABLE$')
        with mock.patch.dict(os.environ):
            os.environ.pop('STACV_UNSET_TEST_VARIABLE', None)
            oInterface = interface_config.read_interface_config(self.sInterfaceFile)
            with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
                interface_config.resolve_timing_reports(oInterface, self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_port_and_file_if_timing_report_does_not_exist(self):
        sMissingFile = os.path.join(self.sDirectory, 'O_DAC_CSF_timing.rpt')
        lText = []
        lText.append('description = "Second port lists a timing report that does not exist"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append(self.sValidPort)
        lText.append('[[port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lText.append(f'timing_reports = ["{sMissingFile}"]')
        self.write_interface_file('\n'.join(lText) + '\n')

        oInterface = interface_config.read_interface_config(self.sInterfaceFile)

        sError = self.build_error_pattern('interface_config_006', 'key "timing_reports" in port O_DAC_CSF names a file that does not exist: ' + re.escape(sMissingFile) + '$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.resolve_timing_reports(oInterface, self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_expanded_path_if_timing_report_does_not_exist(self):
        lText = []
        lText.append('description = "Second port lists a timing report that does not exist using an environment variable"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append(self.sValidPort)
        lText.append('[[port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lText.append('timing_reports = ["$STACV_TEST_REPORT_DIRECTORY/O_DAC_CSF_timing.rpt"]')
        self.write_interface_file('\n'.join(lText) + '\n')

        sMissingFile = os.path.join(self.sDirectory, 'O_DAC_CSF_timing.rpt')
        sError = self.build_error_pattern('interface_config_006', 'key "timing_reports" in port O_DAC_CSF names a file that does not exist: ' + re.escape(sMissingFile) + '$')
        with mock.patch.dict(os.environ, {'STACV_TEST_REPORT_DIRECTORY': self.sDirectory}):
            oInterface = interface_config.read_interface_config(self.sInterfaceFile)
            with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
                interface_config.resolve_timing_reports(oInterface, self.sInterfaceFile)

    def test_read_interface_config_accepts_timing_report_that_does_not_exist(self):
        sMissingFile = os.path.join(self.sDirectory, 'O_DAC_CSF_timing.rpt')
        lText = []
        lText.append('description = "Timing report is not written yet"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append('[[port]]')
        lText.append('name = "O_DAC_CSF"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lText.append(f'timing_reports = ["{sMissingFile}"]')
        self.write_interface_file('\n'.join(lText) + '\n')

        oInterface = interface_config.read_interface_config(self.sInterfaceFile)

        self.assertEqual([sMissingFile], oInterface.ports[0].timing_reports_as_written)

    def test_read_interface_config_resolves_relative_timing_report_against_interface_file_directory(self):
        lText = []
        lText.append('description = "Timing report given relative to the config file"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append('[[port]]')
        lText.append('name = "O_DAC_DATA"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lText.append('timing_reports = ["O_DAC_DATA_timing.rpt"]')
        self.write_interface_file('\n'.join(lText) + '\n')

        sExpectedFile = os.path.join(self.sDirectory, 'O_DAC_DATA_timing.rpt')
        pathlib.Path(sExpectedFile).touch()
        oConfig = interface_config.read_interface_config(self.sInterfaceFile)
        interface_config.resolve_timing_reports(oConfig, self.sInterfaceFile)

        self.assertEqual([sExpectedFile], oConfig.ports[0].timing_reports)

    def test_read_interface_config_raises_error_if_interface_file_does_not_exist(self):
        sError = self.build_error_pattern('interface_config_007', 'does not exist$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_accepts_same_port_with_different_methodologies(self):
        lText = []
        lText.append('description = "Bidirectional port timed with two methodologies"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append(self.build_port('IO_DAC_SDIO', 'SDR-SS-O'))
        lText.append(self.build_port('IO_DAC_SDIO', 'SDR-SS-RT').replace('[[port]]\n', '[[port]]\nstatus = "defer"\n'))
        self.write_interface_file('\n'.join(lText) + '\n')

        oConfig = interface_config.read_interface_config(self.sInterfaceFile)

        lMethodologies = []
        for oPort in oConfig.ports:
            lMethodologies.append(oPort.methodology)
        self.assertEqual(['SDR-SS-O', 'SDR-SS-RT'], lMethodologies)

    def build_config_with_part_and_traces(self, sPart, sTraces):
        lText = []
        lText.append('description = "Part and traces paths"')
        lText.append('name = "DAC_SPI_1"')
        lText.append(f'part = "{sPart}"')
        lText.append(f'traces = "{sTraces}"')
        lText.append(self.sValidPort)
        self.write_interface_file('\n'.join(lText) + '\n')

    def test_read_interface_config_resolves_relative_part_against_interface_file_directory(self):
        self.build_config_with_part_and_traces('part.toml', 'traces.toml')

        oConfig = interface_config.read_interface_config(self.sInterfaceFile)

        self.assertEqual(os.path.join(self.sDirectory, 'part.toml'), oConfig.part)

    def test_read_interface_config_resolves_relative_traces_against_interface_file_directory(self):
        self.build_config_with_part_and_traces('part.toml', 'traces.toml')

        oConfig = interface_config.read_interface_config(self.sInterfaceFile)

        self.assertEqual(os.path.join(self.sDirectory, 'traces.toml'), oConfig.traces)

    def test_read_interface_config_raises_error_naming_variable_if_part_uses_environment_variable_that_is_not_set(self):
        self.build_config_with_part_and_traces('$STACV_UNSET_TEST_VARIABLE/part.toml', 'traces.toml')

        sError = self.build_error_pattern('interface_config_005', 'key "part" uses environment variables that are not set: STACV_UNSET_TEST_VARIABLE$')
        with mock.patch.dict(os.environ):
            os.environ.pop('STACV_UNSET_TEST_VARIABLE', None)
            with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
                interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_variable_if_traces_uses_environment_variable_that_is_not_set(self):
        self.build_config_with_part_and_traces('part.toml', '$STACV_UNSET_TEST_VARIABLE/traces.toml')

        sError = self.build_error_pattern('interface_config_005', 'key "traces" uses environment variables that are not set: STACV_UNSET_TEST_VARIABLE$')
        with mock.patch.dict(os.environ):
            os.environ.pop('STACV_UNSET_TEST_VARIABLE', None)
            with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
                interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_file_if_part_does_not_exist(self):
        self.build_config_with_part_and_traces('missing_part.toml', 'traces.toml')

        sMissingFile = os.path.join(self.sDirectory, 'missing_part.toml')
        sError = self.build_error_pattern('interface_config_006', 'key "part" names a file that does not exist: ' + re.escape(sMissingFile) + '$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_read_interface_config_raises_error_naming_file_if_traces_does_not_exist(self):
        self.build_config_with_part_and_traces('part.toml', 'missing_traces.toml')

        sMissingFile = os.path.join(self.sDirectory, 'missing_traces.toml')
        sError = self.build_error_pattern('interface_config_006', 'key "traces" names a file that does not exist: ' + re.escape(sMissingFile) + '$')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)


class TestClockErrors(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        self.sInterfaceFile = os.path.join(self.sDirectory, 'interface.toml')
        for sFilename in ['part.toml', 'traces.toml']:
            with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
                oFile.write('')

    def write_interface_file(self, lClockNames, sLaunchClock, sCaptureClock):
        lText = []
        lText.append('description = "clock errors"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        for sClockName in lClockNames:
            lText.append('[[clock]]')
            lText.append(f'name = "{sClockName}"')
            lText.append('period = 10.000')
        lText.append('[[port]]')
        lText.append('name = "O_DAC_DATA"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append(f'launch_clock = {{name = "{sLaunchClock}", setup_edge = 8, hold_edge = 0}}')
        lText.append(f'capture_clock = {{name = "{sCaptureClock}", setup_edge = "C", hold_edge = "A"}}')
        lText.append('timing_reports = ["O_DAC_DATA_timing.rpt"]')
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write('\n'.join(lText) + '\n')

    def build_error_pattern(self, sIdentifier, sMessage):
        return r'ERROR: \[' + sIdentifier + r'\] ' + re.escape(self.sInterfaceFile) + ' ' + re.escape(sMessage) + '$'

    def test_raises_error_if_a_launch_clock_is_not_defined(self):
        self.write_interface_file(['dac_sclk'], 'clk_100mhz', 'dac_sclk')
        sError = self.build_error_pattern('interface_config_008', 'key "launch_clock" in port O_DAC_DATA names clock clk_100mhz, which no [[clock]] table defines')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_raises_error_if_a_capture_clock_is_not_defined(self):
        self.write_interface_file(['clk_100mhz'], 'clk_100mhz', 'dac_sclk')
        sError = self.build_error_pattern('interface_config_008', 'key "capture_clock" in port O_DAC_DATA names clock dac_sclk, which no [[clock]] table defines')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_raises_error_if_two_clocks_share_a_name(self):
        self.write_interface_file(['clk_100mhz', 'dac_sclk', 'clk_100mhz'], 'clk_100mhz', 'dac_sclk')
        sError = self.build_error_pattern('interface_config_009', 'clock clk_100mhz is defined by more than one [[clock]] table')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_raises_error_if_a_generator_names_a_master_clock_that_is_not_defined(self):
        lText = []
        lText.append('description = "master clock is not defined"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append('[[clock]]')
        lText.append('name = "dac_sclk"')
        lText.append('period = 40')
        lText.append('port = "O_DAC_SCLK"')
        lText.append('generator = {source = "q_reg", master_pin = "C", target_pin = "Q", master_clock = "clk_100mhz"}')
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write('\n'.join(lText) + '\n')
        sError = self.build_error_pattern('interface_config_008', 'key "generator" of clock dac_sclk names clock clk_100mhz, which no [[clock]] table defines')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)

    def test_raises_error_if_a_port_describes_its_clock_inline(self):
        lText = []
        lText.append('description = "clock described in the port, the old way"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append('[[port]]')
        lText.append('name = "O_DAC_DATA"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", period = 10.000, setup_edge = 8, hold_edge = 0}')
        lText.append('capture_clock = {port = "O_DAC_SCLK", name = "dac_sclk", period = 50, setup_edge = "C", hold_edge = "A"}')
        lText.append('timing_reports = ["O_DAC_DATA_timing.rpt"]')
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write('\n'.join(lText) + '\n')
        # The clock keys written in the port are reported as unknown, which points at the old way.
        sError = self.build_error_pattern('interface_config_004', 'key "port" in capture_clock of port O_DAC_DATA is not a key stacv reads; the keys are name, setup_edge, hold_edge')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            interface_config.read_interface_config(self.sInterfaceFile)


class TestPortStatus(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        self.sInterfaceFile = os.path.join(self.sDirectory, 'interface.toml')
        for sFilename in ['part.toml', 'traces.toml']:
            with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
                oFile.write('')

    def read_interface_with_port(self, lPortLines):
        lText = []
        lText.append('description = "port status"')
        lText.append('name = "DAC_SPI_1"')
        lText.append('part = "part.toml"')
        lText.append('traces = "traces.toml"')
        lText.append('[[port]]')
        lText.extend(lPortLines)
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write('\n'.join(lText) + '\n')
        return interface_config.read_interface_config(self.sInterfaceFile)

    def build_error_pattern(self, sIdentifier, sMessage):
        return r'ERROR: \[' + sIdentifier + r'\] ' + re.escape(self.sInterfaceFile) + ' ' + re.escape(sMessage) + '$'

    def test_deferred_port_needs_only_a_name_and_status(self):
        oInterface = self.read_interface_with_port(['name = "O_DAC_CSF"', 'status = "defer"'])
        self.assertEqual('defer', oInterface.ports[0].status)

    def test_raises_error_if_status_is_not_analyze_or_defer(self):
        sError = self.build_error_pattern('interface_config_010', 'key "status" in port O_DAC_CSF must be "analyze" or "defer"')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            self.read_interface_with_port(['name = "O_DAC_CSF"', 'status = "deferred"'])

    def test_raises_error_if_status_is_not_a_string(self):
        sError = self.build_error_pattern('interface_config_003', 'key "status" in port O_DAC_CSF must be a non-empty string')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            self.read_interface_with_port(['name = "O_DAC_CSF"', 'status = 7'])

    def build_analyzed_port(self, sMethodology):
        lLines = []
        lLines.append('name = "I_DAC_DATA"')
        lLines.append(f'methodology = "{sMethodology}"')
        lLines.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 0}')
        lLines.append('capture_clock = {name = "dac_sclk", setup_edge = "C", hold_edge = "A"}')
        lLines.append('timing_reports = ["I_DAC_DATA_timing.rpt"]')
        lLines.append('[[clock]]')
        lLines.append('name = "clk_100mhz"')
        lLines.append('period = 10')
        lLines.append('[[clock]]')
        lLines.append('name = "dac_sclk"')
        lLines.append('period = 40')
        lLines.append('port = "O_DAC_SCLK"')
        return lLines

    def test_raises_error_if_an_analyzed_port_names_a_methodology_stacv_does_not_support(self):
        sError = self.build_error_pattern('interface_config_011', 'key "methodology" in port I_DAC_DATA names SDR-SS-I, which stacv does not support; correct it, or defer the port with status = "defer"')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            self.read_interface_with_port(self.build_analyzed_port('SDR-SS-I'))

    def test_raises_error_if_an_analyzed_port_names_a_misspelled_methodology(self):
        sError = self.build_error_pattern('interface_config_011', 'key "methodology" in port I_DAC_DATA names SDR-SS-0, which stacv does not support; correct it, or defer the port with status = "defer"')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, sError):
            self.read_interface_with_port(self.build_analyzed_port('SDR-SS-0'))

    def test_deferred_port_may_name_a_methodology_stacv_does_not_support(self):
        oInterface = self.read_interface_with_port(['name = "I_DAC_DATA"', 'status = "defer"', 'methodology = "SDR-SS-RT"'])
        self.assertEqual('defer', oInterface.ports[0].status)

    def test_deferred_port_keeps_a_methodology_it_names(self):
        oInterface = self.read_interface_with_port(['name = "I_DAC_DATA"', 'status = "defer"', 'methodology = "SDR-SS-RT"'])
        self.assertEqual('SDR-SS-RT', oInterface.ports[0].methodology)

