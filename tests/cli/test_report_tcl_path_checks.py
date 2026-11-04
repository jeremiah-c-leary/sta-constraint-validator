import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__

BANNER = '###############################################################################'


def build_interface_text(lPorts):
    lText = []
    lText.append('description = "report script path checks test"')
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
    for sName, sStatus, sTimingReports in lPorts:
        lText.append('')
        lText.append('[[port]]')
        lText.append(f'status = "{sStatus}"')
        lText.append(f'name = "{sName}"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_launch", setup_edge = 8, hold_edge = 8}')
        lText.append('capture_clock = {name = "clk_capture", setup_edge = "D", hold_edge = "B"}')
        lText.append('registers = ["q_spi_output_data_reg"]')
        lText.append(f'timing_reports = {sTimingReports}')
    return '\n'.join(lText) + '\n'


def build_banner(sTitle):
    return [BANNER, f'# {sTitle}', BANNER]


def build_variable_check(sVariable):
    lLines = []
    lLines.append(f'if {{![info exists env({sVariable})]}} {{')
    lLines.append(f'    error "stacv: environment variable {sVariable} is not set"')
    lLines.append('}')
    return lLines


def build_directory_check(sPort, sDirectory):
    lLines = []
    lLines.append(f'# {sPort}')
    lLines.append(f'if {{![file isdirectory "{sDirectory}"]}} {{')
    lLines.append(f'    error "stacv: {sPort} report directory does not exist: {sDirectory}"')
    lLines.append('}')
    return lLines


class TestReportTclPathChecks(unittest.TestCase):
    '''
    The report script checks its environment variables and report directories
    before it changes the corners, because Vivado does not create directories.
    '''

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        sWorkingDir = os.getcwd()
        self.addCleanup(os.chdir, sWorkingDir)
        os.chdir(oTemporaryDirectory.name)
        os.mkdir('interfaces')
        self.write_file('interfaces/part.toml', '')
        self.write_file('interfaces/traces.toml', '')
        # The variables do not need to be set where stacv runs.
        oEnvironment = mock.patch.dict(os.environ)
        oEnvironment.start()
        self.addCleanup(oEnvironment.stop)
        for sVariable in ['REPORT_DIR', 'SCRATCH_DIR']:
            os.environ.pop(sVariable, None)

    def write_file(self, sFilename, sText):
        with open(sFilename, 'w') as oFile:
            oFile.write(sText)

    def run_generate_report_tcl(self, lPorts):
        self.write_file('interfaces/interface.toml', build_interface_text(lPorts))
        oStdout = io.StringIO()
        with mock.patch('sys.argv', ['stacv', 'generate', 'report_tcl', 'interfaces/interface.toml']):
            with contextlib.redirect_stdout(oStdout):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        self.assertEqual(0, oContext.exception.code)
        self.lLines = oStdout.getvalue().split('\n')

    def get_header_end(self):
        return self.lLines.index(BANNER, 1)

    def get_header_tail(self):
        # The lines after the Purpose text, up to the banner that closes the header.
        iPurposeEnd = self.lLines.index('#             for each corner. Each port will have its own file.')
        return self.lLines[iPurposeEnd + 1:self.get_header_end() + 1]

    def get_checks(self):
        # The lines between the header and the Slow Corner banner.
        iSlowCorner = self.lLines.index('# Slow Corner')
        return self.lLines[self.get_header_end() + 1:iSlowCorner - 1]

    def test_one_variable_is_required_and_checked_before_the_directories(self):
        self.run_generate_report_tcl([('O_DATA', 'analyze', '["$REPORT_DIR/vivado/O_DATA_timing.rpt"]')])
        self.assertEqual(['#', '# Requires:   REPORT_DIR', '#', BANNER], self.get_header_tail())
        lExpected = ['']
        lExpected.extend(build_banner('Verify Environment Variables Exist'))
        lExpected.extend(build_variable_check('REPORT_DIR'))
        lExpected.append('')
        lExpected.extend(build_banner('Verify Report Directories Exist'))
        lExpected.extend(build_directory_check('O_DATA', '$env(REPORT_DIR)/vivado'))
        lExpected.append('')
        self.assertEqual(lExpected, self.get_checks())

    def test_variables_are_listed_once_in_the_order_they_first_appear(self):
        lPorts = []
        lPorts.append(('O_DATA', 'analyze', '["$SCRATCH_DIR/${REPORT_DIR}/O_DATA_timing.rpt"]'))
        lPorts.append(('O_CS', 'analyze', '["$REPORT_DIR/O_CS_timing.rpt"]'))
        self.run_generate_report_tcl(lPorts)
        self.assertEqual(['#', '# Requires:   SCRATCH_DIR', '#             REPORT_DIR', '#', BANNER], self.get_header_tail())
        lExpected = ['']
        lExpected.extend(build_banner('Verify Environment Variables Exist'))
        lExpected.extend(build_variable_check('SCRATCH_DIR'))
        lExpected.extend(build_variable_check('REPORT_DIR'))
        lExpected.append('')
        lExpected.extend(build_banner('Verify Report Directories Exist'))
        lExpected.extend(build_directory_check('O_DATA', '$env(SCRATCH_DIR)/$env(REPORT_DIR)'))
        lExpected.extend(build_directory_check('O_CS', '$env(REPORT_DIR)'))
        lExpected.append('')
        self.assertEqual(lExpected, self.get_checks())

    def test_absolute_path_has_no_variable_section(self):
        self.run_generate_report_tcl([('O_DATA', 'analyze', '["/reports/O_DATA_timing.rpt"]')])
        self.assertEqual(['#', BANNER], self.get_header_tail())
        lExpected = ['']
        lExpected.extend(build_banner('Verify Report Directories Exist'))
        lExpected.extend(build_directory_check('O_DATA', '/reports'))
        lExpected.append('')
        self.assertEqual(lExpected, self.get_checks())

    def test_relative_path_directory_is_written_from_the_directory_stacv_runs_in(self):
        self.run_generate_report_tcl([('O_DATA', 'analyze', '["timing_reports/O_DATA_timing.rpt"]')])
        lExpected = ['']
        lExpected.extend(build_banner('Verify Report Directories Exist'))
        lExpected.extend(build_directory_check('O_DATA', 'interfaces/timing_reports'))
        lExpected.append('')
        self.assertEqual(lExpected, self.get_checks())

    def test_each_analyzed_port_is_checked_and_deferred_ports_are_not(self):
        lPorts = []
        lPorts.append(('O_DATA', 'analyze', '["/reports/O_DATA_timing.rpt"]'))
        lPorts.append(('O_CS', 'defer', '["$SCRATCH_DIR/O_CS_timing.rpt"]'))
        lPorts.append(('O_LDAC', 'analyze', '["/reports/O_LDAC_timing.rpt"]'))
        self.run_generate_report_tcl(lPorts)
        self.assertEqual(['#', BANNER], self.get_header_tail())
        lExpected = ['']
        lExpected.extend(build_banner('Verify Report Directories Exist'))
        lExpected.extend(build_directory_check('O_DATA', '/reports'))
        lExpected.extend(build_directory_check('O_LDAC', '/reports'))
        lExpected.append('')
        self.assertEqual(lExpected, self.get_checks())

    def test_every_port_deferred_has_no_checks(self):
        self.run_generate_report_tcl([('O_DATA', 'defer', '["$REPORT_DIR/O_DATA_timing.rpt"]')])
        self.assertEqual(['#', BANNER], self.get_header_tail())
        self.assertEqual([''], self.get_checks())
