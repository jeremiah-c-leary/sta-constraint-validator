import argparse
import contextlib
import datetime
import io
import os
import tempfile
import unittest

from stacv import version
from stacv.cli import check

sTestDir = os.path.dirname(os.path.abspath(__file__))
sParseDir = os.path.join(sTestDir, '..', 'timing_report', 'parse', 'vivado')
sRuleDir = os.path.join(sTestDir, '..', 'rules', 'timing_report')

sPassingReport = os.path.abspath(os.path.join(sParseDir, 'O_DAC_DATA_timing.rpt'))
sFailingReport = os.path.abspath(os.path.join(sRuleDir, 's0_timing_report_002.failing.rpt'))


def build_config_text(lTimingReports):
    lText = []
    lText.append('description = "check.py test"')
    lText.append('[[interface]]')
    lText.append('name = "DAC_SPI_1"')
    for iPort, sTimingReport in enumerate(lTimingReports, start=1):
        lText.append('[[interface.port]]')
        lText.append(f'name = "PORT_{iPort}"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append(f'timing_reports = ["{sTimingReport}"]')
    return '\n'.join(lText)


class TestExecute(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sConfigFile = os.path.join(self.oTempDir.name, 'stacv.toml')

    def tearDown(self):
        self.oTempDir.cleanup()

    def execute_with_reports(self, lTimingReports):
        with open(self.sConfigFile, 'w') as oFile:
            oFile.write(build_config_text(lTimingReports))
        oArgs = argparse.Namespace(config_file=self.sConfigFile, report=None)
        oDateTime = datetime.datetime(2026, 10, 17, 21, 14, 53)
        lArgv = ['stacv', 'check', self.sConfigFile]
        with contextlib.redirect_stdout(io.StringIO()):
            return check.execute(oArgs, oDateTime, lArgv)

    def test_execute_returns_zero_when_every_rule_passes(self):
        self.assertEqual(0, self.execute_with_reports([sPassingReport]))

    def test_execute_returns_one_when_any_rule_fails(self):
        self.assertEqual(1, self.execute_with_reports([sFailingReport]))

    def test_execute_returns_one_when_a_later_port_fails(self):
        self.assertEqual(1, self.execute_with_reports([sPassingReport, sFailingReport]))


class TestExecuteReportHeader(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sConfigFile = os.path.join(self.oTempDir.name, 'stacv.toml')
        self.sReportFile = os.path.join(self.oTempDir.name, 'stacv_report.txt')
        self.oDateTime = datetime.datetime(2026, 10, 17, 21, 14, 53)

    def tearDown(self):
        self.oTempDir.cleanup()

    def execute_with_argv(self, lArgv):
        with open(self.sConfigFile, 'w') as oFile:
            oFile.write(build_config_text([sPassingReport]))
        oArgs = argparse.Namespace(config_file=self.sConfigFile, report=self.sReportFile)
        with contextlib.redirect_stdout(io.StringIO()):
            check.execute(oArgs, self.oDateTime, lArgv)

    def read_report_header(self):
        with open(self.sReportFile, 'r') as oFile:
            lLines = oFile.readlines()
        return lLines[0:6]

    def build_argv(self, sProgram):
        return [sProgram, 'check', self.sConfigFile, '--report', self.sReportFile]

    def test_report_starts_with_header(self):
        self.execute_with_argv(self.build_argv('stacv'))
        lExpected = []
        lExpected.append('-' * 80 + '\n')
        lExpected.append('STA Constraint Validator check report\n')
        lExpected.append(f'Version {version.VERSION}\n')
        lExpected.append('Date:  2026-10-17 21:14:53\n')
        lExpected.append(f'Command:  stacv check {self.sConfigFile} --report {self.sReportFile}\n')
        lExpected.append('-' * 80 + '\n')
        self.assertEqual(lExpected, self.read_report_header())

    def test_header_command_shows_program_name_without_path(self):
        self.execute_with_argv(self.build_argv('/home/user/stacv/bin/stacv'))
        sExpected = f'Command:  stacv check {self.sConfigFile} --report {self.sReportFile}\n'
        self.assertEqual(sExpected, self.read_report_header()[4])
