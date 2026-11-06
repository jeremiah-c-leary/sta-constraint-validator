import contextlib
import io
import os
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sFixtureDir = os.path.join(sProjectDir, 'tests', 'cli', 'fixtures', 'dac81404_failing')
sTimingReport = 'tests/fixtures/dac81404/timing_reports/O_DAC_DATA_timing.rpt'


class TestFailingExample(unittest.TestCase):
    '''
    The DAC81404 example after its data trace changed.
    The output delays in its timing report were calculated for the old trace, so they do not match the new one.
    '''

    def setUp(self):
        # The console shows paths relative to where stacv runs.
        sStartDirectory = os.getcwd()
        os.chdir(sProjectDir)
        self.addCleanup(os.chdir, sStartDirectory)
        sInterfaceFile = os.path.join(sFixtureDir, 'interface.toml')
        self.oStdout = io.StringIO()
        with mock.patch('sys.argv', ['stacv', 'check', sInterfaceFile]):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        self.iExitCode = oContext.exception.code

    def test_check_exits_with_one(self):
        self.assertEqual(1, self.iExitCode)

    def test_check_fails_only_the_output_delay_rules(self):
        lFailedLines = []
        for sLine in self.oStdout.getvalue().split('\n'):
            if sLine.startswith('FAILED:'):
                lFailedLines.append(sLine)
        self.assertEqual(['FAILED: [s3_output_delay_001] O_DAC_DATA.SDR-SS-O', 'FAILED: [s3_output_delay_002] O_DAC_DATA.SDR-SS-O'], lFailedLines)

    def test_console_shows_each_failing_rule_with_its_details(self):
        lExpected = []
        lExpected.append('Reading interface file tests/cli/fixtures/dac81404_failing/interface.toml')
        lExpected.append(f'Reading timing report file {sTimingReport}')
        lExpected.append('FAILED: [s3_output_delay_001] O_DAC_DATA.SDR-SS-O')
        lExpected.append(f'    {sTimingReport}:24  Calculated maximum output delay is 13.000ns while actual output delay is 12.000ns')
        lExpected.append('FAILED: [s3_output_delay_002] O_DAC_DATA.SDR-SS-O')
        lExpected.append(f'    {sTimingReport}:101  Calculated minimum output delay is -11.000ns while actual output delay is -12.000ns')
        lExpected.append('DEFERRED: O_DAC_CSF')
        lExpected.append('DEFERRED: I_DAC_DATA')
        lExpected.append('')
        self.assertEqual('\n'.join(lExpected), self.oStdout.getvalue())
