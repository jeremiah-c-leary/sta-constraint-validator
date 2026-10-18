import argparse
import contextlib
import io
import os
import tempfile
import unittest

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
        with contextlib.redirect_stdout(io.StringIO()):
            return check.execute(oArgs)

    def test_execute_returns_zero_when_every_rule_passes(self):
        self.assertEqual(0, self.execute_with_reports([sPassingReport]))

    def test_execute_returns_one_when_any_rule_fails(self):
        self.assertEqual(1, self.execute_with_reports([sFailingReport]))

    def test_execute_returns_one_when_a_later_port_fails(self):
        self.assertEqual(1, self.execute_with_reports([sPassingReport, sFailingReport]))
