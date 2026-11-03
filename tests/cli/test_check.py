import argparse
import contextlib
import datetime
import hashlib
import io
import os
import shutil
import tempfile
import unittest
import xml.etree.ElementTree

from stacv import version
from stacv.cli import check
from stacv.interface import interface_config_error
from stacv.rules.output_delay import s2_output_delay_001
from stacv.rules.timing_report import s0_timing_report_002

# A port given this instead of a timing report is written as a deferred port.
DEFERRED = None

sTestDir = os.path.dirname(os.path.abspath(__file__))
sRuleDir = os.path.join(sTestDir, '..', 'rules', 'timing_report')

sPassingReport = os.path.abspath(os.path.join(sTestDir, '..', '..', 'example', 'texas_instruments', 'DAC81404', 'timing_reports', 'O_DAC_DATA_timing.rpt'))
sFailingReport = os.path.abspath(os.path.join(sRuleDir, 's0_timing_report_002.failing.rpt'))
sOutputDelayFailingReport = os.path.abspath(os.path.join(sTestDir, '..', 'rules', 'output_delay', 's2_output_delay_001.failing.rpt'))


def build_config_text(lTimingReports, sTracesFile, sPartFile):
    lText = []
    lText.append('description = "check.py test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append('part_interface = "Serial Interface"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.extend(build_clock_tables())
    for iPort, sTimingReport in enumerate(lTimingReports, start=1):
        lText.append('[[port]]')
        lText.append(f'name = "PORT_{iPort}"')
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 8}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "D", hold_edge = "B"}')
        lText.append(f'timing_reports = ["{sTimingReport}"]')
    return '\n'.join(lText)


def build_clock_tables():
    lText = []
    lText.append('[[clock]]')
    lText.append('name = "clk_100mhz"')
    lText.append('period = 10.000')
    lText.append('[[clock]]')
    lText.append('name = "dac_sclk"')
    lText.append('period = 40.0')
    lText.append('port = "O_DAC_SCLK"')
    return lText


def build_numbered_port_names(lTimingReports):
    lPortNames = []
    for iPort in range(1, len(lTimingReports) + 1):
        lPortNames.append(f'PORT_{iPort}')
    return lPortNames


def get_port_names(lPorts):
    lPortNames = []
    for sPortName, sTimingReport in lPorts:
        lPortNames.append(sPortName)
    return lPortNames


def write_numbered_port_timing_reports(sDirectory, lTimingReports):
    lPortTimingReports = []
    for iPort, sTimingReport in enumerate(lTimingReports, start=1):
        lPortTimingReports.append(write_port_timing_report(sDirectory, f'PORT_{iPort}', sTimingReport))
    return lPortTimingReports


def write_named_port_timing_reports(sDirectory, lPorts):
    lPortTimingReports = []
    for sPortName, sTimingReport in lPorts:
        lPortTimingReports.append((sPortName, write_port_timing_report(sDirectory, sPortName, sTimingReport)))
    return lPortTimingReports


def write_port_timing_report(sDirectory, sPortName, sTimingReport):
    # The fixture timing reports time the port O_DAC_DATA.
    # The copy times sPortName instead, so the port passes the same rules as the fixture.
    if not is_fixture_timing_report(sTimingReport):
        return sTimingReport
    sPortTimingReport = build_port_timing_report_filename(sDirectory, sPortName, sTimingReport)
    with open(sTimingReport, newline='') as oFile:
        sText = oFile.read()
    with open(sPortTimingReport, 'w', newline='') as oFile:
        oFile.write(sText.replace('O_DAC_DATA', sPortName))
    return sPortTimingReport


def is_fixture_timing_report(sTimingReport):
    return sTimingReport in [sPassingReport, sFailingReport, sOutputDelayFailingReport]


def build_port_timing_report_filename(sDirectory, sPortName, sTimingReport):
    return os.path.join(sDirectory, f'{sPortName}_{os.path.basename(sTimingReport)}')


def build_traces_text(lPortNames):
    # Every port connects to part pin SDIN.  With the part setup and hold of 10,
    # the calculated output delays match the output delays in sPassingReport:
    #    maximum:   10 + 3.0 - 1.0 =  12.000
    #    minimum:  -10 + 1.0 - 3.0 = -12.000
    lText = []
    for sPortName in lPortNames:
        lText.extend(build_trace_text(sPortName, 'SDIN', 3.0, 1.0))
    lText.extend(build_trace_text('O_DAC_SCLK', 'SCLK', 3.0, 1.0))
    return '\n'.join(lText)


def build_trace_text(sDevicePin, sPartPin, fMaxDelay, fMinDelay):
    lText = []
    lText.append('[[trace]]')
    lText.append(f'name = "{sDevicePin}"')
    lText.append(f'device_pin = "{sDevicePin}"')
    lText.append(f'part_pin = "{sPartPin}"')
    lText.append(f'device_to_part = {{max_delay = {fMaxDelay}, min_delay = {fMinDelay}}}')
    return lText


def build_part_text():
    lText = []
    lText.append('[properties]')
    lText.append('manufacturer = "Texas Instruments"')
    lText.append('part_number = "DAC81404"')
    lText.append('')
    lText.append('[datasheet]')
    lText.append('name = "DACx1401 Quad, 16-Bit and 12-Bit, High-Voltage-Output DACs With Internal Reference"')
    lText.append('url = "https://www.ti.com/lit/ds/symlink/dac81404.pdf"')
    lText.append('version = "SLASEH2A -- November 2020 -- REVISED MAY 2021"')
    lText.append('')
    lText.append('[[interface]]')
    lText.append('name = "Serial Interface"')
    lText.append('')
    lText.append('[[interface.pin]]')
    lText.append('name = "SDIN"')
    lText.append('methodology = "SDR-SS-I"')
    lText.append('clock = {pin = "SCLK", max_frequency = 25}')
    lText.append('capture_edge = "Falling"')
    lText.append('setup = {value = 10, symbol = "tSDIS", source = "Table 7.6"}')
    lText.append('hold = {value = 10, symbol = "tSDIH", source = "Table 7.6"}')
    lText.append('')
    lText.append('[[interface.pin]]')
    lText.append('name = "SDO"')
    lText.append('methodology = "SDR-SS-RT-DO"')
    lText.append('clock = {pin = "SCLK", max_frequency = 12.5}')
    lText.append('cko_max = {value = 30, symbol = "tSDODLY", source = "Table 7.8"}')
    lText.append('cko_min = {value = 0, symbol = "tSDODLY", source = "Table 7.8"}')
    lText.append('launch_edge = "Rising"')
    return '\n'.join(lText)


class TestExecute(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sInterfaceFile = os.path.join(self.oTempDir.name, 'interface.toml')
        self.sTracesFile = os.path.join(self.oTempDir.name, 'traces.toml')
        self.sPartFile = os.path.join(self.oTempDir.name, 'part.toml')

    def tearDown(self):
        self.oTempDir.cleanup()

    def execute_with_reports(self, lTimingReports):
        lTimingReports = write_numbered_port_timing_reports(self.oTempDir.name, lTimingReports)
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(build_config_text(lTimingReports, self.sTracesFile, self.sPartFile))
        with open(self.sTracesFile, 'w') as oFile:
            oFile.write(build_traces_text(build_numbered_port_names(lTimingReports)))
        with open(self.sPartFile, 'w') as oFile:
            oFile.write(build_part_text())
        oArgs = argparse.Namespace(interface_file=self.sInterfaceFile, report=None, junit=None)
        oDateTime = datetime.datetime(2026, 10, 17, 21, 14, 53)
        lArgv = ['stacv', 'check', self.sInterfaceFile]
        with contextlib.redirect_stdout(io.StringIO()):
            return check.execute(oArgs, oDateTime, lArgv)

    def test_execute_raises_error_if_timing_report_does_not_exist(self):
        sMissingReport = os.path.join(self.oTempDir.name, 'missing_timing.rpt')
        with self.assertRaisesRegex(interface_config_error.InterfaceConfigError, 'interface_config_006'):
            self.execute_with_reports([sMissingReport])

    def test_execute_returns_zero_when_every_rule_passes(self):
        self.assertEqual(0, self.execute_with_reports([sPassingReport]))

    def test_execute_returns_one_when_any_rule_fails(self):
        self.assertEqual(1, self.execute_with_reports([sFailingReport]))

    def test_execute_returns_one_when_a_later_port_fails(self):
        self.assertEqual(1, self.execute_with_reports([sPassingReport, sFailingReport]))


class TestExecuteReportHeader(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sInterfaceFile = os.path.join(self.oTempDir.name, 'interface.toml')
        self.sTracesFile = os.path.join(self.oTempDir.name, 'traces.toml')
        self.sPartFile = os.path.join(self.oTempDir.name, 'part.toml')
        self.sReportFile = os.path.join(self.oTempDir.name, 'stacv_report.txt')
        self.oDateTime = datetime.datetime(2026, 10, 17, 21, 14, 53)

    def tearDown(self):
        self.oTempDir.cleanup()

    def execute_with_argv(self, lArgv):
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(build_config_text([sPassingReport], self.sTracesFile, self.sPartFile))
        with open(self.sTracesFile, 'w') as oFile:
            oFile.write(build_traces_text(build_numbered_port_names([sPassingReport])))
        with open(self.sPartFile, 'w') as oFile:
            oFile.write(build_part_text())
        oArgs = argparse.Namespace(interface_file=self.sInterfaceFile, report=self.sReportFile, junit=None)
        with contextlib.redirect_stdout(io.StringIO()):
            check.execute(oArgs, self.oDateTime, lArgv)

    def read_report_header(self):
        with open(self.sReportFile, 'r') as oFile:
            lLines = oFile.readlines()
        return lLines[0:6]

    def build_argv(self, sProgram):
        return [sProgram, 'check', self.sInterfaceFile, '--report', self.sReportFile]

    def test_report_starts_with_header(self):
        self.execute_with_argv(self.build_argv('stacv'))
        lExpected = []
        lExpected.append('-' * 80 + '\n')
        lExpected.append('STA Constraint Validator check report\n')
        lExpected.append(f'Version {version.VERSION}\n')
        lExpected.append('Date:  2026-10-17 21:14:53\n')
        lExpected.append(f'Command:  stacv check {self.sInterfaceFile} --report {self.sReportFile}\n')
        lExpected.append('-' * 80 + '\n')
        self.assertEqual(lExpected, self.read_report_header())

    def test_header_command_shows_program_name_without_path(self):
        self.execute_with_argv(self.build_argv('/home/user/stacv/bin/stacv'))
        sExpected = f'Command:  stacv check {self.sInterfaceFile} --report {self.sReportFile}\n'
        self.assertEqual(sExpected, self.read_report_header()[4])


def build_named_ports_config_text(sDescription, lPorts, sTracesFile, sPartFile):
    lText = []
    lText.append(f'description = "{sDescription}"')
    lText.append('name = "DAC_SPI_1"')
    lText.append(f'part = "{sPartFile}"')
    lText.append('part_interface = "Serial Interface"')
    lText.append(f'traces = "{sTracesFile}"')
    lText.extend(build_clock_tables())
    for sPortName, sTimingReport in lPorts:
        lText.append('[[port]]')
        lText.append(f'name = "{sPortName}"')
        if sTimingReport == DEFERRED:
            lText.append('status = "defer"')
            continue
        lText.append('methodology = "SDR-SS-O"')
        lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 8}')
        lText.append('capture_clock = {name = "dac_sclk", setup_edge = "D", hold_edge = "B"}')
        lText.append(f'timing_reports = ["{sTimingReport}"]')
    return '\n'.join(lText)


class TestExecuteReportTableOfContents(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sInterfaceFile = os.path.join(self.oTempDir.name, 'interface.toml')
        self.sTracesFile = os.path.join(self.oTempDir.name, 'traces.toml')
        self.sPartFile = os.path.join(self.oTempDir.name, 'part.toml')
        self.sReportFile = os.path.join(self.oTempDir.name, 'stacv_report.txt')

    def tearDown(self):
        self.oTempDir.cleanup()

    def execute_with_ports(self, lPorts):
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(build_named_ports_config_text('Table of contents test', lPorts, self.sTracesFile, self.sPartFile))
        with open(self.sTracesFile, 'w') as oFile:
            oFile.write(build_traces_text(get_port_names(lPorts)))
        with open(self.sPartFile, 'w') as oFile:
            oFile.write(build_part_text())
        oArgs = argparse.Namespace(interface_file=self.sInterfaceFile, report=self.sReportFile, junit=None)
        oDateTime = datetime.datetime(2026, 10, 17, 21, 14, 53)
        lArgv = ['stacv', 'check', self.sInterfaceFile, '--report', self.sReportFile]
        with contextlib.redirect_stdout(io.StringIO()):
            check.execute(oArgs, oDateTime, lArgv)

    def read_report_lines(self):
        with open(self.sReportFile, 'r') as oFile:
            return oFile.read().splitlines()

    def test_table_of_contents_follows_header_and_lists_every_section_and_port(self):
        lPorts = []
        lPorts.append(('P1', sFailingReport))
        lPorts.append(('P2', sPassingReport))
        self.execute_with_ports(lPorts)

        lExpected = []
        lExpected.append('-' * 80)
        lExpected.append('')
        lExpected.append('Table of Contents')
        lExpected.append('')
        lExpected.append('Section 1: Summary')
        lExpected.append('Section 2: Inputs')
        lExpected.append('Section 3: Port Rule Checks')
        lExpected.append('Section 3.1: P1.SDR-SS-O Rule Checks')
        lExpected.append('Section 3.2: P2.SDR-SS-O Rule Checks')
        lExpected.append('')
        lExpected.append('=' * 80)
        lExpected.append('Section 1: Summary')
        self.assertEqual(lExpected, self.read_report_lines()[5:17])

    def test_table_of_contents_entries_each_title_a_section_later_in_the_report(self):
        lPorts = []
        lPorts.append(('O_DAC_DATA', sFailingReport))
        lPorts.append(('O_DAC_CSF', sPassingReport))
        lPorts.append(('O_DAC_CLK', sPassingReport))
        self.execute_with_ports(lPorts)

        lLines = self.read_report_lines()
        iFirstEntry = lLines.index('Table of Contents') + 2
        iLastEntry = find_first_blank_line(lLines, iFirstEntry)
        lBody = lLines[iLastEntry:]
        for sEntry in lLines[iFirstEntry:iLastEntry]:
            iTitle = lBody.index(sEntry)
            self.assertIn(lBody[iTitle - 1], ['=' * 80, '-' * 80])


class TestExecuteReportSummary(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sInterfaceFile = os.path.join(self.oTempDir.name, 'interface.toml')
        self.sTracesFile = os.path.join(self.oTempDir.name, 'traces.toml')
        self.sPartFile = os.path.join(self.oTempDir.name, 'part.toml')
        self.sReportFile = os.path.join(self.oTempDir.name, 'stacv_report.txt')

    def tearDown(self):
        self.oTempDir.cleanup()

    def execute_with_config_text(self, sConfigText, lPortNames):
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(sConfigText)
        with open(self.sTracesFile, 'w') as oFile:
            oFile.write(build_traces_text(lPortNames))
        with open(self.sPartFile, 'w') as oFile:
            oFile.write(build_part_text())
        oArgs = argparse.Namespace(interface_file=self.sInterfaceFile, report=self.sReportFile, junit=None)
        oDateTime = datetime.datetime(2026, 10, 17, 21, 14, 53)
        lArgv = ['stacv', 'check', self.sInterfaceFile, '--report', self.sReportFile]
        with contextlib.redirect_stdout(io.StringIO()):
            check.execute(oArgs, oDateTime, lArgv)

    def read_summary_section(self):
        with open(self.sReportFile, 'r') as oFile:
            lLines = oFile.read().splitlines()
        iStart = find_section_title(lLines, 'Section 1: Summary') - 1
        iTableHeader = find_first_line_starting_with(lLines, 'Port ', iStart)
        iEnd = find_first_blank_line(lLines, iTableHeader)
        return lLines[iStart:iEnd]

    def test_summary_lists_interface_and_every_port(self):
        lPorts = []
        lPorts.append(('P1', sFailingReport))
        lPorts.append(('P2', sPassingReport))
        lPorts = write_named_port_timing_reports(self.oTempDir.name, lPorts)
        self.execute_with_config_text(build_named_ports_config_text('This interface is a summary test', lPorts, self.sTracesFile, self.sPartFile), get_port_names(lPorts))

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
        lPorts = write_named_port_timing_reports(self.oTempDir.name, lPorts)
        self.execute_with_config_text(build_named_ports_config_text('Long port names', lPorts, self.sTracesFile, self.sPartFile), get_port_names(lPorts))

        lExpected = []
        lExpected.append('Port         Methodology   Report Key            Section   Result')
        lExpected.append('----------   -----------   -------------------   -------   ------')
        lExpected.append('O_DAC_DATA   SDR-SS-O      O_DAC_DATA.SDR-SS-O   3.1       Failed')
        lExpected.append('O_DAC_CSF    SDR-SS-O      O_DAC_CSF.SDR-SS-O    3.2       Passed')
        self.assertEqual(lExpected, self.read_summary_section()[7:])



    def execute_with_a_deferred_port(self):
        lPorts = []
        lPorts.append(('P1', sPassingReport))
        lPorts.append(('P2', DEFERRED))
        lPorts.append(('P3', sFailingReport))
        lPorts = write_named_port_timing_reports(self.oTempDir.name, lPorts)
        self.execute_with_config_text(build_named_ports_config_text('One port deferred', lPorts, self.sTracesFile, self.sPartFile), get_port_names(lPorts))

    def read_report_lines(self):
        with open(self.sReportFile, 'r') as oFile:
            return oFile.read().splitlines()

    def test_summary_lists_a_deferred_port_without_a_section(self):
        self.execute_with_a_deferred_port()
        lExpected = []
        lExpected.append('Port   Methodology   Report Key    Section   Result')
        lExpected.append('----   -----------   -----------   -------   --------')
        lExpected.append('P1     SDR-SS-O      P1.SDR-SS-O   3.1       Passed')
        lExpected.append('P2' + ' ' * 19 + 'P2' + ' ' * 12 + '-' + ' ' * 9 + 'Deferred')
        lExpected.append('P3     SDR-SS-O      P3.SDR-SS-O   3.2       Failed')
        self.assertEqual(lExpected, self.read_summary_section()[7:])

    def test_summary_shows_the_methodology_a_deferred_port_names(self):
        lPorts = []
        lPorts.append(('P1', sPassingReport))
        lPorts = write_named_port_timing_reports(self.oTempDir.name, lPorts)
        sConfigText = build_named_ports_config_text('Deferred port with a methodology', lPorts, self.sTracesFile, self.sPartFile)
        sConfigText += '\n[[port]]\nname = "P2"\nstatus = "defer"\nmethodology = "SDR-SS-RT-DI"\n'
        self.execute_with_config_text(sConfigText, get_port_names(lPorts))
        lExpected = []
        lExpected.append('Port   Methodology    Report Key        Section   Result')
        lExpected.append('----   ------------   ---------------   -------   --------')
        lExpected.append('P1     SDR-SS-O       P1.SDR-SS-O       3.1       Passed')
        lExpected.append('P2     SDR-SS-RT-DI   P2.SDR-SS-RT-DI   -         Deferred')
        self.assertEqual(lExpected, self.read_summary_section()[7:])

    def test_rule_check_sections_number_only_the_analyzed_ports(self):
        self.execute_with_a_deferred_port()
        lLines = self.read_report_lines()
        self.assertEqual(2, lLines.count('Section 3.1: P1.SDR-SS-O Rule Checks'))
        self.assertEqual(2, lLines.count('Section 3.2: P3.SDR-SS-O Rule Checks'))
        for sLine in lLines:
            self.assertNotIn('Section 3.3', sLine)

class TestExecuteReportInputs(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sInterfaceFile = os.path.join(self.oTempDir.name, 'interface.toml')
        self.sTracesFile = os.path.join(self.oTempDir.name, 'traces.toml')
        self.sPartFile = os.path.join(self.oTempDir.name, 'part.toml')
        self.sReportFile = os.path.join(self.oTempDir.name, 'stacv_report.txt')

    def tearDown(self):
        self.oTempDir.cleanup()

    def execute_with_ports(self, lPorts):
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(build_named_ports_config_text('Inputs test', lPorts, self.sTracesFile, self.sPartFile))
        with open(self.sTracesFile, 'w') as oFile:
            oFile.write(build_traces_text(get_port_names(lPorts)))
        with open(self.sPartFile, 'w') as oFile:
            oFile.write(build_part_text())
        oArgs = argparse.Namespace(interface_file=self.sInterfaceFile, report=self.sReportFile, junit=None)
        oDateTime = datetime.datetime(2026, 10, 17, 21, 14, 53)
        lArgv = ['stacv', 'check', self.sInterfaceFile, '--report', self.sReportFile]
        with contextlib.redirect_stdout(io.StringIO()):
            check.execute(oArgs, oDateTime, lArgv)

    def read_inputs_section(self):
        with open(self.sReportFile, 'r') as oFile:
            lLines = oFile.read().splitlines()
        iStart = find_section_title(lLines, 'Section 2: Inputs') - 1
        iTableHeader = find_first_line_starting_with(lLines, 'md5sum ', iStart)
        iEnd = find_first_blank_line(lLines, iTableHeader)
        return lLines[iStart:iEnd]

    def copy_passing_report_to(self, sBasename):
        sTimingReport = os.path.join(self.oTempDir.name, sBasename)
        shutil.copyfile(sPassingReport, sTimingReport)
        return sTimingReport

    def test_inputs_list_interface_file_then_timing_reports_in_declaration_order(self):
        lPorts = []
        lPorts.append(('P1', sPassingReport))
        lPorts.append(('P2', sFailingReport))
        self.execute_with_ports(lPorts)

        iWidth = max(len(self.sInterfaceFile), len(sPassingReport), len(sFailingReport))
        if iWidth + 34 > 80:
            iWidth = 80 - 34
        lExpected = []
        lExpected.append('=' * 80)
        lExpected.append('Section 2: Inputs')
        lExpected.append('=' * 80)
        lExpected.append('')
        lExpected.append('md5sum' + ' ' * 26 + '  ' + 'Filename')
        lExpected.append('-' * 32 + '  ' + '-' * iWidth)
        lExpected.append(calculate_md5(self.sInterfaceFile) + '  ' + self.sInterfaceFile)
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
        self.assertEqual([self.sInterfaceFile, sPassingReport, sFailingReport], lFilenames)

    def test_inputs_list_a_timing_report_reached_by_two_spellings_of_its_path_once(self):
        sTimingReport = self.copy_passing_report_to('timing.rpt')
        lPorts = []
        lPorts.append(('P1', 'timing.rpt'))
        lPorts.append(('P2', './timing.rpt'))
        self.execute_with_ports(lPorts)

        lFilenames = []
        for sLine in self.read_inputs_section()[6:]:
            lFilenames.append(sLine.split('  ', 1)[1])
        self.assertEqual([self.sInterfaceFile, sTimingReport], lFilenames)

    def test_inputs_list_a_timing_report_reached_by_two_spellings_of_its_absolute_path_once(self):
        sTimingReport = self.copy_passing_report_to('timing.rpt')
        lPorts = []
        lPorts.append(('P1', sTimingReport))
        lPorts.append(('P2', os.path.join(self.oTempDir.name, '.', 'timing.rpt')))
        self.execute_with_ports(lPorts)

        lFilenames = []
        for sLine in self.read_inputs_section()[6:]:
            lFilenames.append(sLine.split('  ', 1)[1])
        self.assertEqual([self.sInterfaceFile, sTimingReport], lFilenames)

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


class TestExecuteReportRuleChecks(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sInterfaceFile = os.path.join(self.oTempDir.name, 'interface.toml')
        self.sTracesFile = os.path.join(self.oTempDir.name, 'traces.toml')
        self.sPartFile = os.path.join(self.oTempDir.name, 'part.toml')
        self.sReportFile = os.path.join(self.oTempDir.name, 'stacv_report.txt')

    def tearDown(self):
        self.oTempDir.cleanup()

    def execute_with_ports(self, lPorts):
        lPorts = write_named_port_timing_reports(self.oTempDir.name, lPorts)
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(build_named_ports_config_text('Rule checks test', lPorts, self.sTracesFile, self.sPartFile))
        with open(self.sTracesFile, 'w') as oFile:
            oFile.write(build_traces_text(get_port_names(lPorts)))
        with open(self.sPartFile, 'w') as oFile:
            oFile.write(build_part_text())
        oArgs = argparse.Namespace(interface_file=self.sInterfaceFile, report=self.sReportFile, junit=None)
        oDateTime = datetime.datetime(2026, 10, 17, 21, 14, 53)
        lArgv = ['stacv', 'check', self.sInterfaceFile, '--report', self.sReportFile]
        with contextlib.redirect_stdout(io.StringIO()):
            check.execute(oArgs, oDateTime, lArgv)

    def read_rule_checks_section(self):
        with open(self.sReportFile, 'r') as oFile:
            lLines = oFile.read().splitlines()
        iStart = find_section_title(lLines, 'Section 3: Port Rule Checks') - 1
        return lLines[iStart:]

    def read_port_rule_checks(self, sSectionTitle):
        lLines = self.read_rule_checks_section()
        iStart = lLines.index(sSectionTitle) - 1
        iEnd = find_first_blank_line(lLines, iStart)
        return lLines[iStart:iEnd]

    def test_rule_checks_list_every_rule_of_a_passing_port_by_stage(self):
        lPorts = []
        lPorts.append(('P1', sPassingReport))
        self.execute_with_ports(lPorts)

        lExpected = []
        lExpected.append('=' * 80)
        lExpected.append('Section 3: Port Rule Checks')
        lExpected.append('=' * 80)
        lExpected.append('')
        lExpected.append('-' * 80)
        lExpected.append('Section 3.1: P1.SDR-SS-O Rule Checks')
        lExpected.append('-' * 80)
        lExpected.append('Rule                  Result   Details')
        lExpected.append('- stage 0 ' + '-' * 70)
        lExpected.append('s0_timing_report_001  Passed')
        lExpected.append('s0_timing_report_002  Passed')
        lExpected.append('s0_trace_001          Passed')
        lExpected.append('s0_data_path_001      Passed')
        lExpected.append('s0_clock_path_001     Passed')
        lExpected.append('s0_register_001       Passed')
        lExpected.append('s0_register_002       Passed')
        lExpected.append('s0_register_003       Passed')
        lExpected.append('- stage 1 ' + '-' * 70)
        lExpected.append('s1_clock_001          Passed')
        lExpected.append('- stage 2 ' + '-' * 70)
        lExpected.append('s2_clock_001          Passed')
        lExpected.append('s2_clock_002          Passed')
        lExpected.append('s2_output_delay_001   Passed')
        lExpected.append('s2_output_delay_002   Passed')
        lExpected.append('- stage 3 ' + '-' * 70)
        lExpected.append('s3_output_delay_001   Passed')
        lExpected.append('s3_output_delay_002   Passed')
        lExpected.append('- stage 4 ' + '-' * 70)
        lExpected.append('s4_capture_clock_001  Passed')
        lExpected.append('s4_capture_clock_002  Passed')
        lExpected.append('s4_launch_clock_001   Passed')
        lExpected.append('s4_launch_clock_002   Passed')
        lExpected.append('s4_part_001           Passed')
        lExpected.append('s4_requirement_001    Passed')
        lExpected.append('s4_requirement_002    Passed')
        lExpected.append('- stage 5 ' + '-' * 70)
        lExpected.append('s5_slack_001          Passed')
        lExpected.append('s5_slack_002          Passed')
        lExpected.append('-' * 80)
        self.assertEqual(lExpected, self.read_rule_checks_section())

    def test_rule_checks_show_failure_details_and_skip_reason_for_later_stages(self):
        lPorts = []
        lPorts.append(('P1', sFailingReport))
        self.execute_with_ports(lPorts)
        sTimingReport = build_port_timing_report_filename(self.oTempDir.name, 'P1', sFailingReport)

        lExpected = []
        lExpected.append('Rule                  Result   Details')
        lExpected.append('- stage 0 ' + '-' * 70)
        lExpected.append('s0_timing_report_001  Passed')
        lExpected.append('s0_timing_report_002  Failed   ' + sTimingReport + ':14  hold timing report, Fast process corner')
        lExpected.append('s0_trace_001          Passed')
        lExpected.append('s0_data_path_001      Passed')
        lExpected.append('s0_clock_path_001     Passed')
        lExpected.append('s0_register_001       Passed')
        lExpected.append('s0_register_002       Passed')
        lExpected.append('s0_register_003       Passed')
        lExpected.append('- stage 1 ' + '-' * 70)
        lExpected.append('s1_clock_001          Skipped  stage 0 failed')
        lExpected.append('- stage 2 ' + '-' * 70)
        lExpected.append('s2_clock_001          Skipped  stage 0 failed')
        lExpected.append('s2_clock_002          Skipped  stage 0 failed')
        lExpected.append('s2_output_delay_001   Skipped  stage 0 failed')
        lExpected.append('s2_output_delay_002   Skipped  stage 0 failed')
        lExpected.append('- stage 3 ' + '-' * 70)
        lExpected.append('s3_output_delay_001   Skipped  stage 0 failed')
        lExpected.append('s3_output_delay_002   Skipped  stage 0 failed')
        lExpected.append('- stage 4 ' + '-' * 70)
        lExpected.append('s4_capture_clock_001  Skipped  stage 0 failed')
        lExpected.append('s4_capture_clock_002  Skipped  stage 0 failed')
        lExpected.append('s4_launch_clock_001   Skipped  stage 0 failed')
        lExpected.append('s4_launch_clock_002   Skipped  stage 0 failed')
        lExpected.append('s4_part_001           Skipped  stage 0 failed')
        lExpected.append('s4_requirement_001    Skipped  stage 0 failed')
        lExpected.append('s4_requirement_002    Skipped  stage 0 failed')
        lExpected.append('- stage 5 ' + '-' * 70)
        lExpected.append('s5_slack_001          Skipped  stage 0 failed')
        lExpected.append('s5_slack_002          Skipped  stage 0 failed')
        lExpected.append('-' * 80)
        self.assertEqual(lExpected, self.read_port_rule_checks('Section 3.1: P1.SDR-SS-O Rule Checks')[3:])

    def test_rule_checks_align_each_detail_line_with_the_details_column(self):
        lPorts = []
        lPorts.append(('P1', sOutputDelayFailingReport))
        self.execute_with_ports(lPorts)
        sTimingReport = build_port_timing_report_filename(self.oTempDir.name, 'P1', sOutputDelayFailingReport)

        lExpected = []
        lExpected.append('s2_output_delay_001   Failed   ' + sTimingReport + ':85  2.000ns')
        lExpected.append(' ' * 31 + sTimingReport + ':229  2.500ns')
        lExpected.append('s2_output_delay_002   Passed')
        self.assertEqual(lExpected, self.read_port_rule_checks('Section 3.1: P1.SDR-SS-O Rule Checks')[18:21])

    def test_rule_checks_give_each_port_its_own_numbered_section_separated_by_a_blank_line(self):
        lPorts = []
        lPorts.append(('P1', sFailingReport))
        lPorts.append(('P2', sPassingReport))
        self.execute_with_ports(lPorts)

        lLines = self.read_rule_checks_section()
        iFirstPortEnd = lLines.index('Section 3.2: P2.SDR-SS-O Rule Checks') - 3
        lExpected = []
        lExpected.append('-' * 80)
        lExpected.append('')
        lExpected.append('-' * 80)
        lExpected.append('Section 3.2: P2.SDR-SS-O Rule Checks')
        lExpected.append('-' * 80)
        self.assertEqual(lExpected, lLines[iFirstPortEnd:iFirstPortEnd + 5])
        self.assertEqual('-' * 80, lLines[-1])


class TestExecuteJunit(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.sInterfaceFile = os.path.join(self.oTempDir.name, 'interface.toml')
        self.sTracesFile = os.path.join(self.oTempDir.name, 'traces.toml')
        self.sPartFile = os.path.join(self.oTempDir.name, 'part.toml')
        self.sJunitFile = os.path.join(self.oTempDir.name, 'stacv_junit.xml')

    def tearDown(self):
        self.oTempDir.cleanup()

    def execute_with_ports(self, lPorts):
        lPorts = write_named_port_timing_reports(self.oTempDir.name, lPorts)
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(build_named_ports_config_text('JUnit test', lPorts, self.sTracesFile, self.sPartFile))
        with open(self.sTracesFile, 'w') as oFile:
            oFile.write(build_traces_text(get_port_names(lPorts)))
        with open(self.sPartFile, 'w') as oFile:
            oFile.write(build_part_text())
        oArgs = argparse.Namespace(interface_file=self.sInterfaceFile, report=None, junit=self.sJunitFile)
        oDateTime = datetime.datetime(2026, 10, 17, 21, 14, 53)
        lArgv = ['stacv', 'check', self.sInterfaceFile, '--junit', self.sJunitFile]
        with contextlib.redirect_stdout(io.StringIO()):
            return check.execute(oArgs, oDateTime, lArgv)

    def read_junit_root(self):
        return xml.etree.ElementTree.parse(self.sJunitFile).getroot()

    def find_testcase(self, sSuiteName, sRuleId):
        for oSuite in self.read_junit_root().findall('testsuite'):
            if oSuite.get('name') == sSuiteName:
                for oTestcase in oSuite.findall('testcase'):
                    if oTestcase.get('name') == sRuleId:
                        return oTestcase
        raise ValueError(f'{sSuiteName} {sRuleId} is not in the JUnit file')

    def test_junit_deferred_port_has_one_skipped_testcase(self):
        lPorts = []
        lPorts.append(('P1', sPassingReport))
        lPorts.append(('P2', DEFERRED))
        self.execute_with_ports(lPorts)
        oTestcase = self.find_testcase('P2', 'deferred')
        self.assertEqual('port is deferred', oTestcase.find('skipped').get('message'))

    def test_junit_file_has_one_testsuite_per_port_named_by_report_key(self):
        lPorts = []
        lPorts.append(('P1', sFailingReport))
        lPorts.append(('P2', sPassingReport))
        self.execute_with_ports(lPorts)

        oRoot = self.read_junit_root()
        lSuiteNames = []
        for oSuite in oRoot.findall('testsuite'):
            lSuiteNames.append(oSuite.get('name'))
        self.assertEqual('testsuites', oRoot.tag)
        self.assertEqual(['P1.SDR-SS-O', 'P2.SDR-SS-O'], lSuiteNames)

    def test_junit_testsuite_has_one_testcase_per_rule_named_by_rule_id(self):
        lPorts = []
        lPorts.append(('P1', sPassingReport))
        self.execute_with_ports(lPorts)

        oSuite = self.read_junit_root().find('testsuite')
        lNames = []
        lClassnames = []
        for oTestcase in oSuite.findall('testcase'):
            lNames.append(oTestcase.get('name'))
            lClassnames.append(oTestcase.get('classname'))
        lExpected = []
        lExpected.append('s0_timing_report_001')
        lExpected.append('s0_timing_report_002')
        lExpected.append('s0_trace_001')
        lExpected.append('s0_data_path_001')
        lExpected.append('s0_clock_path_001')
        lExpected.append('s0_register_001')
        lExpected.append('s0_register_002')
        lExpected.append('s0_register_003')
        lExpected.append('s1_clock_001')
        lExpected.append('s2_clock_001')
        lExpected.append('s2_clock_002')
        lExpected.append('s2_output_delay_001')
        lExpected.append('s2_output_delay_002')
        lExpected.append('s3_output_delay_001')
        lExpected.append('s3_output_delay_002')
        lExpected.append('s4_capture_clock_001')
        lExpected.append('s4_capture_clock_002')
        lExpected.append('s4_launch_clock_001')
        lExpected.append('s4_launch_clock_002')
        lExpected.append('s4_part_001')
        lExpected.append('s4_requirement_001')
        lExpected.append('s4_requirement_002')
        lExpected.append('s5_slack_001')
        lExpected.append('s5_slack_002')
        self.assertEqual(lExpected, lNames)
        self.assertEqual(['P1.SDR-SS-O'] * len(lExpected), lClassnames)

    def test_junit_passing_testcase_is_empty(self):
        lPorts = []
        lPorts.append(('P1', sPassingReport))
        self.execute_with_ports(lPorts)

        oTestcase = self.find_testcase('P1.SDR-SS-O', 's0_timing_report_001')
        self.assertEqual([], list(oTestcase))

    def test_junit_failing_testcase_has_rule_violation_as_message(self):
        lPorts = []
        lPorts.append(('P1', sFailingReport))
        self.execute_with_ports(lPorts)

        oTestcase = self.find_testcase('P1.SDR-SS-O', 's0_timing_report_002')
        oFailure = oTestcase.find('failure')
        self.assertEqual(s0_timing_report_002.FAILURE_MESSAGE, oFailure.get('message'))

    def test_junit_failing_testcase_has_one_detail_per_line_as_body(self):
        lPorts = []
        lPorts.append(('P1', sOutputDelayFailingReport))
        self.execute_with_ports(lPorts)
        sTimingReport = build_port_timing_report_filename(self.oTempDir.name, 'P1', sOutputDelayFailingReport)

        oTestcase = self.find_testcase('P1.SDR-SS-O', 's2_output_delay_001')
        oFailure = oTestcase.find('failure')
        lExpected = []
        lExpected.append(sTimingReport + ':85  2.000ns')
        lExpected.append(sTimingReport + ':229  2.500ns')
        self.assertEqual(s2_output_delay_001.FAILURE_MESSAGE, oFailure.get('message'))
        self.assertEqual('\n'.join(lExpected), oFailure.text)

    def test_junit_skipped_testcase_has_skip_reason_as_message(self):
        lPorts = []
        lPorts.append(('P1', sFailingReport))
        self.execute_with_ports(lPorts)

        oTestcase = self.find_testcase('P1.SDR-SS-O', 's1_clock_001')
        oSkipped = oTestcase.find('skipped')
        self.assertEqual('stage 0 failed', oSkipped.get('message'))
        self.assertIsNone(oSkipped.text)
        self.assertIsNone(oTestcase.find('failure'))

    def test_junit_option_does_not_change_exit_code(self):
        lPorts = []
        lPorts.append(('P1', sPassingReport))
        self.assertEqual(0, self.execute_with_ports(lPorts))
        lPorts = []
        lPorts.append(('P1', sFailingReport))
        self.assertEqual(1, self.execute_with_ports(lPorts))


def find_section_title(lLines, sTitle):
    for iLine in range(1, len(lLines)):
        if lLines[iLine] == sTitle and lLines[iLine - 1] == '=' * 80:
            return iLine
    raise ValueError(f'{sTitle} is not a section title')


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
