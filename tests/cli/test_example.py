import contextlib
import io
import os
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sInterfaceFile = 'example/texas_instruments/DAC81404/interface.toml'
sConstraintsFile = 'example/constraints.xdc'
sReportScriptFile = 'example/dac_spi_1_stacv_report.tcl'


class TestExample(unittest.TestCase):
    '''
    The DAC81404 example is run from the project directory, as a user would,
    so the paths in its constraints file match the paths written in the example.
    '''

    def setUp(self):
        sWorkingDir = os.getcwd()
        self.addCleanup(os.chdir, sWorkingDir)
        os.chdir(sProjectDir)
        # The example's timing_reports start with $PROJ_DIR, as a user's flow would set it.
        oEnvironment = mock.patch.dict(os.environ, {'PROJ_DIR': sProjectDir})
        oEnvironment.start()
        self.addCleanup(oEnvironment.stop)

    def run_stacv(self, lArguments):
        oStdout = io.StringIO()
        with mock.patch('sys.argv', ['stacv'] + lArguments):
            with contextlib.redirect_stdout(oStdout):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code, oStdout.getvalue()

    def test_generated_constraints_match_the_example_constraints_file(self):
        iExitCode, sOutput = self.run_stacv(['generate', 'xdc', sInterfaceFile])
        with open(sConstraintsFile) as oFile:
            sExpected = oFile.read()
        self.assertEqual(0, iExitCode)
        self.assertEqual(sExpected, sOutput)

    def test_check_passes_the_example_timing_reports(self):
        iExitCode, sOutput = self.run_stacv(['check', sInterfaceFile])
        self.assertEqual(0, iExitCode)
        self.assertTrue(sOutput.endswith('Check Passed\n'))

    def test_check_shows_a_result_for_every_port(self):
        iExitCode, sOutput = self.run_stacv(['check', sInterfaceFile])
        lExpected = []
        lExpected.append(f'Reading interface file {sInterfaceFile}')
        lExpected.append('Reading timing report file example/texas_instruments/DAC81404/timing_reports/O_DAC_DATA_timing.rpt')
        lExpected.append('PASSED: O_DAC_DATA.SDR-SS-O')
        lExpected.append('Reading timing report file example/texas_instruments/DAC81404/timing_reports/O_DAC_SDEN_F_timing.rpt')
        lExpected.append('PASSED: O_DAC_SDEN_F.SDR-SS-O-FLC')
        lExpected.append('Reading timing report file example/texas_instruments/DAC81404/timing_reports/I_DAC_DATA_timing.rpt')
        lExpected.append('PASSED: I_DAC_DATA.SDR-SS-RT')
        lExpected.append('Check Passed')
        lExpected.append('')
        self.assertEqual('\n'.join(lExpected), sOutput)

    def test_generated_report_script_matches_the_example_report_script(self):
        # Runs the command in the script's header, so the file is put back however the test ends.
        with open(sReportScriptFile) as oFile:
            sExpected = oFile.read()
        self.addCleanup(self.write_report_script, sExpected)
        iExitCode, sOutput = self.run_stacv(['generate', 'report_tcl', sInterfaceFile, '--output', sReportScriptFile])
        with open(sReportScriptFile) as oFile:
            sGenerated = oFile.read()
        self.assertEqual(0, iExitCode)
        self.assertEqual(f'Creating report script {sReportScriptFile}\n', sOutput)
        self.assertEqual(sExpected, sGenerated)

    def write_report_script(self, sText):
        with open(sReportScriptFile, 'w') as oFile:
            oFile.write(sText)
