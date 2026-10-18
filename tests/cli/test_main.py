import contextlib
import io
import os
import re
import tempfile
import unittest
from unittest import mock

from stacv import __main__
from tests.cli.test_check import build_config_text
from tests.cli.test_check import sFailingReport
from tests.cli.test_check import sPassingReport


def build_two_interface_config_text(sFirstTimingReport, sSecondTimingReport):
    lText = []
    lText.append('description = "check.py test"')
    lText.append('[[interface]]')
    lText.append('name = "DAC_SPI_1"')
    lText.append('[[interface.port]]')
    lText.append('name = "PORT_1"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append(f'timing_reports = ["{sFirstTimingReport}"]')
    lText.append('[[interface]]')
    lText.append('name = "DAC_SPI_2"')
    lText.append('[[interface.port]]')
    lText.append('name = "PORT_1"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append(f'timing_reports = ["{sSecondTimingReport}"]')
    return '\n'.join(lText)


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

    def test_check_exits_with_one_when_a_failing_port_is_followed_by_a_passing_port(self):
        self.assertEqual(1, self.run_main_with_reports([sFailingReport, sPassingReport]))


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

    def run_main_with_config_text(self, sConfigText):
        with open(self.sConfigFile, 'w') as oFile:
            oFile.write(sConfigText)
        lArgv = ['stacv', 'check', self.sConfigFile]
        with mock.patch('sys.argv', lArgv):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def create_empty_timing_report(self):
        sTimingReport = os.path.join(self.oTempDir.name, 'empty.rpt')
        with open(sTimingReport, 'w'):
            pass
        return sTimingReport

    def test_failing_rule_is_summarised(self):
        self.run_main_with_reports([sFailingReport])
        lExpected = []
        lExpected.append(f'Reading configuration file {self.sConfigFile}\n')
        lExpected.append(f'Reading timing report file {sFailingReport}\n')
        lExpected.append('FAILED: [s0_timing_report_002]\n')
        self.assertEqual(''.join(lExpected), self.oStdout.getvalue())

    def test_failing_port_does_not_stop_later_ports(self):
        self.run_main_with_reports([sFailingReport, sPassingReport])
        lExpected = []
        lExpected.append(f'Reading configuration file {self.sConfigFile}\n')
        lExpected.append(f'Reading timing report file {sFailingReport}\n')
        lExpected.append('FAILED: [s0_timing_report_002]\n')
        lExpected.append(f'Reading timing report file {sPassingReport}\n')
        self.assertEqual(''.join(lExpected), self.oStdout.getvalue())

    def test_every_failing_port_is_reported(self):
        self.run_main_with_reports([sFailingReport, sFailingReport])
        lExpected = []
        lExpected.append(f'Reading configuration file {self.sConfigFile}\n')
        lExpected.append(f'Reading timing report file {sFailingReport}\n')
        lExpected.append('FAILED: [s0_timing_report_002]\n')
        lExpected.append(f'Reading timing report file {sFailingReport}\n')
        lExpected.append('FAILED: [s0_timing_report_002]\n')
        self.assertEqual(''.join(lExpected), self.oStdout.getvalue())

    def test_failing_interface_does_not_stop_later_interfaces(self):
        self.run_main_with_config_text(build_two_interface_config_text(sFailingReport, sPassingReport))
        lExpected = []
        lExpected.append(f'Reading configuration file {self.sConfigFile}\n')
        lExpected.append(f'Reading timing report file {sFailingReport}\n')
        lExpected.append('FAILED: [s0_timing_report_002]\n')
        lExpected.append(f'Reading timing report file {sPassingReport}\n')
        self.assertEqual(''.join(lExpected), self.oStdout.getvalue())

    def test_failing_later_port_reports_a_failure(self):
        self.run_main_with_reports([sPassingReport, sFailingReport])
        lExpected = []
        lExpected.append(f'Reading configuration file {self.sConfigFile}\n')
        lExpected.append(f'Reading timing report file {sPassingReport}\n')
        lExpected.append(f'Reading timing report file {sFailingReport}\n')
        lExpected.append('FAILED: [s0_timing_report_002]\n')
        self.assertEqual(''.join(lExpected), self.oStdout.getvalue())

    def test_failing_run_writes_nothing_to_stderr(self):
        self.run_main_with_reports([sFailingReport])
        self.assertEqual('', self.oStderr.getvalue())

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


class TestMainReportFile(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sConfigFile = os.path.join(self.oTempDir.name, 'stacv.toml')
        self.sReportFile = os.path.join(self.oTempDir.name, 'stacv_report.txt')
        self.oStdout = io.StringIO()

    def tearDown(self):
        self.oTempDir.cleanup()

    def run_main_with_report_option(self, lTimingReports):
        with open(self.sConfigFile, 'w') as oFile:
            oFile.write(build_config_text(lTimingReports))
        lArgv = ['stacv', 'check', self.sConfigFile, '--report', self.sReportFile]
        with mock.patch('sys.argv', lArgv):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def test_report_file_is_created_when_every_rule_passes(self):
        self.run_main_with_report_option([sPassingReport])
        self.assertTrue(os.path.isfile(self.sReportFile))

    def test_report_file_is_created_when_a_rule_fails(self):
        self.run_main_with_report_option([sFailingReport])
        self.assertTrue(os.path.isfile(self.sReportFile))

    def test_report_option_does_not_change_exit_code(self):
        self.assertEqual(0, self.run_main_with_report_option([sPassingReport]))
        self.assertEqual(1, self.run_main_with_report_option([sFailingReport]))

    def test_creating_report_is_written_after_reading_timing_reports(self):
        self.run_main_with_report_option([sPassingReport])
        lExpected = []
        lExpected.append(f'Reading configuration file {self.sConfigFile}\n')
        lExpected.append(f'Reading timing report file {sPassingReport}\n')
        lExpected.append(f'Creating report {self.sReportFile}\n')
        self.assertEqual(''.join(lExpected), self.oStdout.getvalue())

    def test_creating_report_is_written_after_failed_rules(self):
        self.run_main_with_report_option([sFailingReport])
        lExpected = []
        lExpected.append(f'Reading configuration file {self.sConfigFile}\n')
        lExpected.append(f'Reading timing report file {sFailingReport}\n')
        lExpected.append('FAILED: [s0_timing_report_002]\n')
        lExpected.append(f'Creating report {self.sReportFile}\n')
        self.assertEqual(''.join(lExpected), self.oStdout.getvalue())

    def test_report_header_shows_current_date(self):
        self.run_main_with_report_option([sPassingReport])
        with open(self.sReportFile, 'r') as oFile:
            lLines = oFile.readlines()
        self.assertRegex(lLines[3], re.compile(r'^Date:  \d{4}-\d{2}-\d{2} \d{2}:\d{2}\n$'))

    def test_report_header_shows_command(self):
        self.run_main_with_report_option([sPassingReport])
        with open(self.sReportFile, 'r') as oFile:
            lLines = oFile.readlines()
        sExpected = f'Command:  stacv check {self.sConfigFile} --report {self.sReportFile}\n'
        self.assertEqual(sExpected, lLines[4])
