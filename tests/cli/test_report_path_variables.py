import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sInterfaceFile = 'example/texas_instruments/DAC81404/interface.toml'


class TestReportPathVariables(unittest.TestCase):
    '''
    Only check reads the timing reports, so only check needs the environment
    variables in their paths to be set.  The DAC81404 example's reports start with $PROJ_DIR.
    '''

    def setUp(self):
        sWorkingDir = os.getcwd()
        self.addCleanup(os.chdir, sWorkingDir)
        os.chdir(sProjectDir)
        oEnvironment = mock.patch.dict(os.environ)
        oEnvironment.start()
        self.addCleanup(oEnvironment.stop)
        os.environ.pop('PROJ_DIR', None)

    def run_stacv(self, lArguments):
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv'] + lArguments):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def assert_command_runs_without_proj_dir(self, lCommand):
        iExitCode = self.run_stacv(lCommand + [sInterfaceFile])
        self.assertEqual('', self.oStderr.getvalue())
        self.assertEqual(0, iExitCode)

    def test_visualize_edges_runs_without_proj_dir(self):
        self.assert_command_runs_without_proj_dir(['visualize', 'edges'])

    def test_visualize_block_diagram_runs_without_proj_dir(self):
        self.assert_command_runs_without_proj_dir(['visualize', 'block_diagram'])

    def test_generate_xdc_runs_without_proj_dir(self):
        self.assert_command_runs_without_proj_dir(['generate', 'xdc'])

    def test_generate_report_tcl_runs_without_proj_dir(self):
        self.assert_command_runs_without_proj_dir(['generate', 'report_tcl'])

    def test_generate_report_tcl_writes_proj_dir_for_vivado_to_read(self):
        self.run_stacv(['generate', 'report_tcl', sInterfaceFile])
        self.assertIn('-file "$env(PROJ_DIR)/example/texas_instruments/DAC81404/timing_reports/O_DAC_DATA_timing.rpt"', self.oStdout.getvalue())

    def test_check_needs_proj_dir(self):
        iExitCode = self.run_stacv(['check', sInterfaceFile])
        sExpected = f'ERROR: [interface_config_005] {sInterfaceFile} key "timing_reports" in port O_DAC_DATA uses environment variables that are not set: PROJ_DIR\n'
        self.assertEqual(2, iExitCode)
        self.assertEqual(sExpected, self.oStderr.getvalue())

    def test_part_path_still_needs_its_variable_for_the_block_diagram(self):
        with tempfile.TemporaryDirectory() as sDirectory:
            sFile = os.path.join(sDirectory, 'interface.toml')
            with open(sFile, 'w') as oFile:
                oFile.write('description = "A part path with an unset variable"\n')
                oFile.write('name = "UNSET_PART"\n')
                oFile.write('part = "$PROJ_DIR/part.toml"\n')
                oFile.write('traces = "traces.toml"\n')
                oFile.write('[[port]]\nstatus = "defer"\nname = "O_DATA"\n')
            iExitCode = self.run_stacv(['visualize', 'block_diagram', sFile])
        sExpected = f'ERROR: [interface_config_005] {sFile} key "part" uses environment variables that are not set: PROJ_DIR\n'
        self.assertEqual(2, iExitCode)
        self.assertEqual(sExpected, self.oStderr.getvalue())
