import contextlib
import io
import os
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sInterfaceFile = 'example/texas_instruments/DAC81404/interface.toml'
sConstraintsFile = 'example/constraints.xdc'


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
