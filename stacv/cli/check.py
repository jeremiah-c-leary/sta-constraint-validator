
import os

from stacv import version
from stacv.config import interface_config
from stacv.methodology import methodology_factory
from stacv.results import port_result
from stacv.results import port_result_list
from stacv.timing_report import timing_report_file
from stacv.timing_report import timing_report_list
from stacv.timing_report.xilinx import vivado


def execute(oCmdLine, oDateTime, lArgv):
    print(f'Reading configuration file {oCmdLine.config_file}')
    oInterface = interface_config.read_interface_config(oCmdLine.config_file)
    oPortResults = get_port_results(oInterface)
    if oCmdLine.report is not None:
        write_check_report(oCmdLine.report, oDateTime, lArgv, oInterface, oPortResults)
    if oPortResults.has_failures():
        return 1
    return 0


def get_port_results(oInterface):
    oPortResults = port_result_list.PortResultList()
    for oPort in oInterface.ports:
        oPortResult = get_port_result(oPort)
        oPortResults.add_result(oPortResult)
    return oPortResults


def get_port_result(oPort):
    oMethodology = create_methodology(oPort)
    oTimingReportList = create_timing_reports(oPort.timing_reports)
    oMethodologyResults = oMethodology.check(oTimingReportList)
    print_failing_rules(oMethodologyResults)
    return port_result.PortResult(oPort, oMethodologyResults)


def create_methodology(oPort):
    return methodology_factory.create_methodology(oPort.methodology)


def print_failing_rules(oMethodologyResults):
    for oRuleResult in oMethodologyResults.get_failing_results():
        print(f'FAILED: [{oRuleResult.rule_id}]')


def create_timing_reports(lFilenames):
    oTimingReportList = timing_report_list.TimingReportList()
    for sFilename in lFilenames:
        oTimingReportFile = create_timing_report_file(sFilename)
        oParsedTimingReportList = parse_timing_report(oTimingReportFile)
        merge_timing_reports(oTimingReportList, oParsedTimingReportList)
    return oTimingReportList


def create_timing_report_file(sTimingReport):
    print(f'Reading timing report file {sTimingReport}')
    lLines = read_text_file(sTimingReport)
    return timing_report_file.TimingReportFile(sTimingReport, lLines)


def read_text_file(sFilename):
    with open(sFilename, 'r') as oFile:
        return oFile.readlines()


def parse_timing_report(oTimingReportFile):
    return vivado.parse_timing_report(oTimingReportFile)


def merge_timing_reports(oTimingReportList, oParsedTimingReportList):
    oTimingReportList.extend(oParsedTimingReportList)


def write_check_report(sFilename, oDateTime, lArgv, oInterface, oPortResults):
    print(f'Creating report {sFilename}')
    lLines = []
    lLines.extend(build_header(oDateTime, lArgv))
    lLines.extend(build_section_1(oInterface, oPortResults))
    write_file(sFilename, lLines)


def build_header(oDateTime, lArgv):
    lLines = []
    lLines.append(build_minor_divider())
    lLines.append('STA Constraint Validator check report')
    lLines.append(f'Version {version.VERSION}')
    lLines.append(build_date(oDateTime))
    lLines.append(build_command(lArgv))
    lLines.append(build_minor_divider())
    return lLines


def build_minor_divider():
    return '-'*80


def build_date(oDateTime):
    return f'Date:  {oDateTime.strftime("%Y-%m-%d %H:%M:%S")}'


def build_command(lArgv):
    sCommand = 'Command:  '
    sCommand += os.path.basename(lArgv[0])
    sCommand += ' '
    sCommand += ' '.join(lArgv[1:])
    return sCommand


def build_section_1(oInterface, oPortResults):
    lLines = []
    lLines.append(build_major_divider())
    lLines.append('Section 1: Summary')
    lLines.append(build_major_divider())
    lLines.append('')
    lLines.append(f'Interface:    {oInterface.interface_name}')
    lLines.append(f'Description:  {oInterface.description}')
    lLines.append('')
    lLines.extend(build_table(oPortResults))
    return lLines


def build_major_divider():
    return '='*80


def build_table(oPortResults):
    lTable = build_initial_table(oPortResults)
    lTable = adjust_table_column_widths(lTable)
    lTable = add_separator(lTable)
    lTable = expand_rows(lTable)
    return lTable


def build_initial_table(oPortResults):
    lTable = []
    lTable.append(['Port', 'Methodology', 'Report Key', 'Section', 'Result'])
    for iPortResult, oPortResult in enumerate(oPortResults.results, start=1):
        lRow = [oPortResult.port.name]
        lRow.append(oPortResult.port.methodology)
        lRow.append(lRow[0] + '.' + lRow[1])
        lRow.append('3.' + str(iPortResult))
        if oPortResult.methodology_results.has_failures():
            lRow.append('Failed')
        else:
            lRow.append('Passed')
        lTable.append(lRow)
    return lTable


def adjust_table_column_widths(lTable):
    for iColumn in range(len(lTable[0])):
        iMaxLength = 0
        for lRow in lTable:
            iMaxLength = max(iMaxLength, len(lRow[iColumn]))
        for lRow in lTable:
            lRow[iColumn] += ' ' * (iMaxLength - len(lRow[iColumn]))
    return lTable


def add_separator(lTable):
    lMyTable = lTable
    lRow = []
    for sColumn in lTable[0]:
        lRow.append('-' * len(sColumn))
    lMyTable.insert(1, lRow)
    return lMyTable


def expand_rows(lTable):
    lExpandedTable = []
    for lRow in lTable:
        lExpandedTable.append('   '.join(lRow))
    return lExpandedTable


def write_file(sFilename, lLines):
    with open(sFilename, 'w') as oFile:
        oFile.write('\n'.join(lLines) + '\n')
