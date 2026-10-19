import argparse
import contextlib
import datetime
import hashlib
import io
import os
import shutil
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
    lText.append('interface = "DAC_SPI_1"')
    for iPort, sTimingReport in enumerate(lTimingReports, start=1):
        lText.append('[[port]]')
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


def build_named_ports_config_text(sDescription, lPorts):
    lText = []
    lText.append(f'description = "{sDescription}"')
    lText.append('interface = "DAC_SPI_1"')
    for sPortName, sTimingReport in lPorts:
        lText.append('[[port]]')
        lText.append(f'name = "{sPortName}"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append(f'timing_reports = ["{sTimingReport}"]')
    return '\n'.join(lText)


class TestExecuteReportSummary(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sConfigFile = os.path.join(self.oTempDir.name, 'stacv.toml')
        self.sReportFile = os.path.join(self.oTempDir.name, 'stacv_report.txt')

    def tearDown(self):
        self.oTempDir.cleanup()

    def execute_with_config_text(self, sConfigText):
        with open(self.sConfigFile, 'w') as oFile:
            oFile.write(sConfigText)
        oArgs = argparse.Namespace(config_file=self.sConfigFile, report=self.sReportFile)
        oDateTime = datetime.datetime(2026, 10, 17, 21, 14, 53)
        lArgv = ['stacv', 'check', self.sConfigFile, '--report', self.sReportFile]
        with contextlib.redirect_stdout(io.StringIO()):
            check.execute(oArgs, oDateTime, lArgv)

    def read_summary_section(self):
        with open(self.sReportFile, 'r') as oFile:
            lLines = oFile.read().splitlines()
        iStart = lLines.index('Section 1: Summary') - 1
        iTableHeader = find_first_line_starting_with(lLines, 'Port ', iStart)
        iEnd = find_first_blank_line(lLines, iTableHeader)
        return lLines[iStart:iEnd]

    def test_summary_lists_interface_and_every_port(self):
        lPorts = []
        lPorts.append(('P1', sFailingReport))
        lPorts.append(('P2', sPassingReport))
        self.execute_with_config_text(build_named_ports_config_text('This interface is a summary test', lPorts))

        lExpected = []
        lExpected.append('=' * 80)
        lExpected.append('Section 1: Summary')
        lExpected.append('=' * 80)
        lExpected.append('')
        lExpected.append('Interface:    DAC_SPI_1')
        lExpected.append('Description:  This interface is a summary test')
        lExpected.append('')
        lExpected.append('Port   Methodology   Report Key    Section   Result')
        lExpected.append('----   -----------   -----------   -------   ------')
        lExpected.append('P1     SDR-SS-O      P1.SDR-SS-O   3.1       Failed')
        lExpected.append('P2     SDR-SS-O      P2.SDR-SS-O   3.2       Passed')
        self.assertEqual(lExpected, self.read_summary_section())

    def test_summary_columns_widen_to_the_longest_value(self):
        lPorts = []
        lPorts.append(('O_DAC_DATA', sFailingReport))
        lPorts.append(('O_DAC_CSF', sPassingReport))
        self.execute_with_config_text(build_named_ports_config_text('Long port names', lPorts))

        lExpected = []
        lExpected.append('Port         Methodology   Report Key            Section   Result')
        lExpected.append('----------   -----------   -------------------   -------   ------')
        lExpected.append('O_DAC_DATA   SDR-SS-O      O_DAC_DATA.SDR-SS-O   3.1       Failed')
        lExpected.append('O_DAC_CSF    SDR-SS-O      O_DAC_CSF.SDR-SS-O    3.2       Passed')
        self.assertEqual(lExpected, self.read_summary_section()[7:])



class TestExecuteReportInputs(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sConfigFile = os.path.join(self.oTempDir.name, 'stacv.toml')
        self.sReportFile = os.path.join(self.oTempDir.name, 'stacv_report.txt')

    def tearDown(self):
        self.oTempDir.cleanup()

    def execute_with_ports(self, lPorts):
        with open(self.sConfigFile, 'w') as oFile:
            oFile.write(build_named_ports_config_text('Inputs test', lPorts))
        oArgs = argparse.Namespace(config_file=self.sConfigFile, report=self.sReportFile)
        oDateTime = datetime.datetime(2026, 10, 17, 21, 14, 53)
        lArgv = ['stacv', 'check', self.sConfigFile, '--report', self.sReportFile]
        with contextlib.redirect_stdout(io.StringIO()):
            check.execute(oArgs, oDateTime, lArgv)

    def read_inputs_section(self):
        with open(self.sReportFile, 'r') as oFile:
            lLines = oFile.read().splitlines()
        iStart = lLines.index('Section 2: Inputs') - 1
        iTableHeader = find_first_line_starting_with(lLines, 'md5sum ', iStart)
        iEnd = find_first_blank_line(lLines, iTableHeader)
        return lLines[iStart:iEnd]

    def copy_passing_report_to(self, sBasename):
        sTimingReport = os.path.join(self.oTempDir.name, sBasename)
        shutil.copyfile(sPassingReport, sTimingReport)
        return sTimingReport

    def test_inputs_list_config_file_then_timing_reports_in_declaration_order(self):
        lPorts = []
        lPorts.append(('P1', sPassingReport))
        lPorts.append(('P2', sFailingReport))
        self.execute_with_ports(lPorts)

        iWidth = max(len(self.sConfigFile), len(sPassingReport), len(sFailingReport))
        if iWidth + 34 > 80:
            iWidth = 80 - 34
        lExpected = []
        lExpected.append('=' * 80)
        lExpected.append('Section 2: Inputs')
        lExpected.append('=' * 80)
        lExpected.append('')
        lExpected.append('md5sum' + ' ' * 26 + '  ' + 'Filename')
        lExpected.append('-' * 32 + '  ' + '-' * iWidth)
        lExpected.append(calculate_md5(self.sConfigFile) + '  ' + self.sConfigFile)
        lExpected.append(calculate_md5(sPassingReport) + '  ' + sPassingReport)
        lExpected.append(calculate_md5(sFailingReport) + '  ' + sFailingReport)
        self.assertEqual(lExpected, self.read_inputs_section())

    def test_inputs_list_a_timing_report_used_by_two_ports_once(self):
        lPorts = []
        lPorts.append(('P1', sPassingReport))
        lPorts.append(('P2', sFailingReport))
        lPorts.append(('P3', sPassingReport))
        self.execute_with_ports(lPorts)

        lFilenames = []
        for sLine in self.read_inputs_section()[6:]:
            lFilenames.append(sLine.split('  ', 1)[1])
        self.assertEqual([self.sConfigFile, sPassingReport, sFailingReport], lFilenames)

    def test_inputs_list_a_timing_report_reached_by_two_spellings_of_its_path_once(self):
        sTimingReport = self.copy_passing_report_to('timing.rpt')
        lPorts = []
        lPorts.append(('P1', 'timing.rpt'))
        lPorts.append(('P2', './timing.rpt'))
        self.execute_with_ports(lPorts)

        lFilenames = []
        for sLine in self.read_inputs_section()[6:]:
            lFilenames.append(sLine.split('  ', 1)[1])
        self.assertEqual([self.sConfigFile, sTimingReport], lFilenames)

    def test_inputs_list_a_timing_report_reached_by_two_spellings_of_its_absolute_path_once(self):
        sTimingReport = self.copy_passing_report_to('timing.rpt')
        lPorts = []
        lPorts.append(('P1', sTimingReport))
        lPorts.append(('P2', os.path.join(self.oTempDir.name, '.', 'timing.rpt')))
        self.execute_with_ports(lPorts)

        lFilenames = []
        for sLine in self.read_inputs_section()[6:]:
            lFilenames.append(sLine.split('  ', 1)[1])
        self.assertEqual([self.sConfigFile, sTimingReport], lFilenames)

    def test_inputs_filename_separator_stops_at_80_characters(self):
        sTimingReport = self.copy_passing_report_to('long_timing_report_name_' + 'x' * 80 + '.rpt')
        lPorts = []
        lPorts.append(('P1', sTimingReport))
        self.execute_with_ports(lPorts)

        lInputs = self.read_inputs_section()
        self.assertEqual('-' * 32 + '  ' + '-' * (80 - 34), lInputs[5])

    def test_inputs_show_a_filename_longer_than_80_characters_in_full(self):
        sTimingReport = self.copy_passing_report_to('long_timing_report_name_' + 'x' * 80 + '.rpt')
        lPorts = []
        lPorts.append(('P1', sTimingReport))
        self.execute_with_ports(lPorts)

        lInputs = self.read_inputs_section()
        self.assertEqual(calculate_md5(sTimingReport) + '  ' + sTimingReport, lInputs[7])


def find_first_line_starting_with(lLines, sPrefix, iStart):
    for iLine in range(iStart, len(lLines)):
        if lLines[iLine].startswith(sPrefix):
            return iLine
    return len(lLines)


def find_first_blank_line(lLines, iStart):
    for iLine in range(iStart, len(lLines)):
        if lLines[iLine] == '':
            return iLine
    return len(lLines)


def calculate_md5(sFilename):
    with open(sFilename, 'rb') as oFile:
        return hashlib.md5(oFile.read()).hexdigest()
