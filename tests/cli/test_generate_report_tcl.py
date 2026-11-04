import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__


def build_interface_text(sTimingReports):
    lText = []
    lText.append('description = "report script test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append('part = "part.toml"')
    lText.append('part_interface = "Serial Interface"')
    lText.append('traces = "traces.toml"')
    lText.append('')
    lText.append('[[clock]]')
    lText.append('name = "clk_launch"')
    lText.append('period = 10.0')
    lText.append('')
    lText.append('[[clock]]')
    lText.append('name = "clk_capture"')
    lText.append('period = 40.0')
    lText.append('port = "O_SCLK"')
    lText.append('')
    lText.append('[[port]]')
    lText.append('name = "O_DATA"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append('launch_clock = {name = "clk_launch", setup_edge = 8, hold_edge = 8}')
    lText.append('capture_clock = {name = "clk_capture", setup_edge = "D", hold_edge = "B"}')
    lText.append('registers = ["q_spi_output_data_reg"]')
    lText.append(f'timing_reports = {sTimingReports}')
    return '\n'.join(lText) + '\n'


def build_setup_line(sPath):
    return f'report_timing -column_style variable_width -to [get_clocks clk_capture] -through [get_ports O_DATA] -setup -max_paths 100 -nworst 100 -path full_clock_expanded -file "{sPath}"'


class TestGenerateReportTcl(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        sWorkingDir = os.getcwd()
        self.addCleanup(os.chdir, sWorkingDir)
        os.chdir(self.sDirectory)
        os.mkdir('interfaces')
        self.write_file('interfaces/part.toml', '')
        self.write_file('interfaces/traces.toml', '')
        oEnvironment = mock.patch.dict(os.environ, {'REPORT_DIR': '/reports'})
        oEnvironment.start()
        self.addCleanup(oEnvironment.stop)

    def write_file(self, sFilename, sText):
        with open(sFilename, 'w') as oFile:
            oFile.write(sText)

    def run_generate_report_tcl(self, sTimingReports, lExtraArguments=()):
        self.write_file('interfaces/interface.toml', build_interface_text(sTimingReports))
        lArgv = ['stacv', 'generate', 'report_tcl', 'interfaces/interface.toml'] + list(lExtraArguments)
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', lArgv):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def get_output_lines(self):
        return self.oStdout.getvalue().split('\n')

    def test_script_is_written_to_stdout_without_output(self):
        iExitCode = self.run_generate_report_tcl('["O_DATA_timing.rpt"]')
        self.assertEqual(0, iExitCode)
        self.assertEqual('# Command:    stacv generate report_tcl interfaces/interface.toml', self.get_output_lines()[3])

    def test_environment_variable_is_read_by_tcl(self):
        iExitCode = self.run_generate_report_tcl('["$REPORT_DIR/O_DATA_timing.rpt"]')
        self.assertEqual(0, iExitCode)
        self.assertIn(build_setup_line('$env(REPORT_DIR)/O_DATA_timing.rpt'), self.get_output_lines())

    def test_environment_variable_in_braces_is_read_by_tcl(self):
        iExitCode = self.run_generate_report_tcl('["${REPORT_DIR}/O_DATA_timing.rpt"]')
        self.assertEqual(0, iExitCode)
        self.assertIn(build_setup_line('$env(REPORT_DIR)/O_DATA_timing.rpt'), self.get_output_lines())

    def test_absolute_path_is_written_unchanged(self):
        iExitCode = self.run_generate_report_tcl('["/reports/O_DATA_timing.rpt"]')
        self.assertEqual(0, iExitCode)
        self.assertIn(build_setup_line('/reports/O_DATA_timing.rpt'), self.get_output_lines())

    def test_relative_path_is_written_from_the_directory_stacv_runs_in(self):
        iExitCode = self.run_generate_report_tcl('["timing_reports/O_DATA_timing.rpt"]')
        self.assertEqual(0, iExitCode)
        self.assertIn(build_setup_line('interfaces/timing_reports/O_DATA_timing.rpt'), self.get_output_lines())

    def test_port_with_more_than_one_timing_report_is_an_error(self):
        iExitCode = self.run_generate_report_tcl('["slow.rpt", "fast.rpt"]')
        self.assertEqual(2, iExitCode)
        self.assertEqual('', self.oStdout.getvalue())
        self.assertEqual('ERROR: [generate_010] port O_DATA has 2 timing reports; the report script writes one file for each port\n', self.oStderr.getvalue())

    def test_output_writes_the_script_to_a_file(self):
        iExitCode = self.run_generate_report_tcl('["O_DATA_timing.rpt"]', ['--output', 'report.tcl'])
        self.assertEqual(0, iExitCode)
        self.assertEqual('Creating report script report.tcl\n', self.oStdout.getvalue())
        with open('report.tcl') as oFile:
            self.assertIn(build_setup_line('interfaces/O_DATA_timing.rpt'), oFile.read().split('\n'))
