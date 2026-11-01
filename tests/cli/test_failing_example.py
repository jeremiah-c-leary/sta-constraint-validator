import contextlib
import io
import os
import unittest
from unittest import mock

from stacv import __main__

sFixtureDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'dac81404_failing')


class TestFailingExample(unittest.TestCase):
    '''
    The DAC81404 example after its data trace changed.
    The output delays in its timing report were calculated for the old trace, so they do not match the new one.
    '''

    def setUp(self):
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
        self.assertEqual(['FAILED: [s3_output_delay_001]', 'FAILED: [s3_output_delay_002]'], lFailedLines)
