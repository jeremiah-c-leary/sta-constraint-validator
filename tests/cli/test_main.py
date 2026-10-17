import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__
from tests.cli.test_check import build_config_text
from tests.cli.test_check import sFailingReport
from tests.cli.test_check import sPassingReport


class TestMainCheckDispatch(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sConfigFile = os.path.join(self.oTempDir.name, 'stacv.toml')

    def tearDown(self):
        self.oTempDir.cleanup()

    def run_main_with_reports(self, lTimingReports):
        with open(self.sConfigFile, 'w') as oFile:
            oFile.write(build_config_text(lTimingReports))
        lArgv = ['stacv', 'check', self.sConfigFile]
        with mock.patch('sys.argv', lArgv):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as oContext:
                    __main__.main()
        return oContext.exception.code

    def test_check_exits_with_zero_when_every_rule_passes(self):
        self.assertEqual(0, self.run_main_with_reports([sPassingReport]))

    def test_check_exits_with_one_when_any_rule_fails(self):
        self.assertEqual(1, self.run_main_with_reports([sFailingReport]))
