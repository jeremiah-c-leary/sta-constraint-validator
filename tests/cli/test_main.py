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


class TestMainToolErrors(unittest.TestCase):

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
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def create_empty_timing_report(self):
        sTimingReport = os.path.join(self.oTempDir.name, 'empty.rpt')
        with open(sTimingReport, 'w'):
            pass
        return sTimingReport

    def test_config_error_exits_with_two(self):
        with mock.patch.dict(os.environ):
            os.environ.pop('STACV_UNSET_VARIABLE', None)
            iExitCode = self.run_main_with_reports(['$STACV_UNSET_VARIABLE/report.rpt'])
        self.assertEqual(2, iExitCode)

    def test_timing_report_parse_error_exits_with_two(self):
        iExitCode = self.run_main_with_reports([self.create_empty_timing_report()])
        self.assertEqual(2, iExitCode)


class TestMainConsoleOutput(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sConfigFile = os.path.join(self.oTempDir.name, 'stacv.toml')
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()

    def tearDown(self):
        self.oTempDir.cleanup()

    def run_main_with_reports(self, lTimingReports):
        with open(self.sConfigFile, 'w') as oFile:
            oFile.write(build_config_text(lTimingReports))
        lArgv = ['stacv', 'check', self.sConfigFile]
        with mock.patch('sys.argv', lArgv):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit):
                        __main__.main()

    def create_empty_timing_report(self):
        sTimingReport = os.path.join(self.oTempDir.name, 'empty.rpt')
        with open(sTimingReport, 'w'):
            pass
        return sTimingReport

    def test_passing_run_reports_each_file_read(self):
        self.run_main_with_reports([sPassingReport, sPassingReport])
        lExpected = []
        lExpected.append(f'Reading configuration file {self.sConfigFile}\n')
        lExpected.append(f'Reading timing report file {sPassingReport}\n')
        lExpected.append(f'Reading timing report file {sPassingReport}\n')
        self.assertEqual(''.join(lExpected), self.oStdout.getvalue())

    def test_passing_run_writes_nothing_to_stderr(self):
        self.run_main_with_reports([sPassingReport])
        self.assertEqual('', self.oStderr.getvalue())

    def test_config_error_stops_after_reading_configuration_file(self):
        with mock.patch.dict(os.environ):
            os.environ.pop('STACV_UNSET_VARIABLE', None)
            self.run_main_with_reports(['$STACV_UNSET_VARIABLE/report.rpt'])
        self.assertEqual(f'Reading configuration file {self.sConfigFile}\n', self.oStdout.getvalue())

    def test_config_error_is_written_to_stderr(self):
        with mock.patch.dict(os.environ):
            os.environ.pop('STACV_UNSET_VARIABLE', None)
            self.run_main_with_reports(['$STACV_UNSET_VARIABLE/report.rpt'])
        lExpected = []
        lExpected.append('ERROR: [interface_config_004] ')
        lExpected.append(self.sConfigFile)
        lExpected.append(' key "timing_reports" in interface DAC_SPI_1 port PORT_1')
        lExpected.append(' uses environment variables that are not set: STACV_UNSET_VARIABLE\n')
        self.assertEqual(''.join(lExpected), self.oStderr.getvalue())

    def test_parse_error_stops_after_reading_timing_report_file(self):
        sTimingReport = self.create_empty_timing_report()
        self.run_main_with_reports([sTimingReport])
        lExpected = []
        lExpected.append(f'Reading configuration file {self.sConfigFile}\n')
        lExpected.append(f'Reading timing report file {sTimingReport}\n')
        self.assertEqual(''.join(lExpected), self.oStdout.getvalue())

    def test_parse_error_is_written_to_stderr(self):
        sTimingReport = self.create_empty_timing_report()
        self.run_main_with_reports([sTimingReport])
        sExpected = f'ERROR: [vivado_tr_parse_001] {sTimingReport}:1 No timing reports detected\n'
        self.assertEqual(sExpected, self.oStderr.getvalue())
