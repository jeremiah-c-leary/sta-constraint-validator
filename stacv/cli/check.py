
import hashlib
import os

from stacv import version
from stacv.config import interface_config
from stacv.methodology import methodology_factory
from stacv.results import port_result
from stacv.results import port_result_list
from stacv.timing_report import timing_report_file
from stacv.timing_report import timing_report_list
from stacv.timing_report.xilinx import vivado


REPORT_WIDTH = 80
MD5SUM_COLUMN_WIDTH = 32
COLUMN_GAP = 2
MAXIMUM_FILENAME_COLUMN_WIDTH = REPORT_WIDTH - MD5SUM_COLUMN_WIDTH - COLUMN_GAP
RESULT_COLUMN_WIDTH = len('Skipped')


def execute(oCmdLine, oDateTime, lArgv):
    print(f'Reading configuration file {oCmdLine.config_file}')
    oInterface = interface_config.read_interface_config(oCmdLine.config_file)
    oPortResults = get_port_results(oInterface)
    if oCmdLine.report is not None:
        write_check_report(oCmdLine.report, oDateTime, lArgv, oInterface, oPortResults, oCmdLine.config_file)
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


def write_check_report(sFilename, oDateTime, lArgv, oInterface, oPortResults, sConfigFile):
    print(f'Creating report {sFilename}')
    lLines = []
    lLines.extend(build_header(oDateTime, lArgv))
    lLines.extend(build_section_1(oInterface, oPortResults))
    lLines.append('')
    lLines.extend(build_section_2(oPortResults, sConfigFile))
    lLines.append('')
    lLines.extend(build_section_3(oPortResults))
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
    return '-'*REPORT_WIDTH


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
    return '='*REPORT_WIDTH


def build_table(oPortResults):
    lRows = build_unformatted_table(oPortResults)
    return format_table(lRows)


def build_unformatted_table(oPortResults):
    lTable = []
    lTable.append(['Port', 'Methodology', 'Report Key', 'Section', 'Result'])
    for iPortResult, oPortResult in enumerate(oPortResults.results, start=1):
        lRow = [oPortResult.port.name]
        lRow.append(oPortResult.port.methodology)
        lRow.append(build_report_key(oPortResult))
        lRow.append('3.' + str(iPortResult))
        if oPortResult.methodology_results.has_failures():
            lRow.append('Failed')
        else:
            lRow.append('Passed')
        lTable.append(lRow)
    return lTable


def build_report_key(oPortResult):
    return oPortResult.port.name + '.' + oPortResult.port.methodology


def format_table(lRows):
    lWidths = get_column_widths(lRows)
    lLines = []
    lLines.append(format_row(lRows[0], lWidths))
    lLines.append(build_separator(lWidths))
    for lRow in lRows[1:]:
        lLines.append(format_row(lRow, lWidths))
    return lLines


def get_column_widths(lRows):
    lWidths = []
    for iColumn in range(len(lRows[0])):
        iMaxLength = 0
        for lRow in lRows:
            iMaxLength = max(iMaxLength, len(lRow[iColumn]))
        lWidths.append(iMaxLength)
    return lWidths


def format_row(lRow, lWidths):
    sRow = ''
    for sColumn, iWidth in zip(lRow, lWidths):
        sRow += f'{sColumn:<{iWidth}}   '
    sRow = sRow.rstrip()
    return sRow


def build_separator(lWidths):
    sRow = ''
    for iWidth in lWidths:
        sRow += '-' * iWidth + '   '
    sRow = sRow.rstrip()
    return sRow


def write_file(sFilename, lLines):
    with open(sFilename, 'w') as oFile:
        oFile.write('\n'.join(lLines) + '\n')


def build_section_2(oPortResults, sConfigFile):
    lLines = []
    lLines.extend(build_section_2_header())
    lLines.append('')
    lLines.extend(build_section_2_table(oPortResults, sConfigFile))
    return lLines


def build_section_2_header():
    lLines = []
    lLines.append(build_major_divider())
    lLines.append('Section 2: Inputs')
    lLines.append(build_major_divider())
    return lLines


def build_section_2_table(oPortResults, sConfigFile):
    lFiles = get_input_filenames(oPortResults, sConfigFile)
    lLines = build_md5sum_table_header(lFiles)
    lLines.extend(build_md5sum_table_rows(lFiles))
    return lLines


def get_input_filenames(oPortResults, sConfigFile):
    lFiles = []
    lFiles.append(sConfigFile)
    lFiles.extend(get_unique_timing_report_filenames(oPortResults))
    return lFiles


def get_unique_timing_report_filenames(oPortResults):
    lFilenames = []
    for oPortResult in oPortResults.results:
        for sFilename in oPortResult.port.timing_reports:
            if sFilename not in lFilenames:
                lFilenames.append(sFilename)
    return lFilenames


def build_md5sum_table_header(lFiles):
    lLines = []
    sGap = ' '*COLUMN_GAP
    lLines.append(f'{"md5sum":<{MD5SUM_COLUMN_WIDTH}}{sGap}Filename')
    lLines.append(build_md5sum_separator(lFiles))
    return lLines


def build_md5sum_separator(lFiles):
    iFileColumnWidth = calculate_filename_column_width(lFiles)
    sLine = '-'*MD5SUM_COLUMN_WIDTH + ' '*COLUMN_GAP + '-'*iFileColumnWidth
    return sLine


def calculate_filename_column_width(lFiles):
    iFileColumnWidth = len('Filename')
    for sFile in lFiles:
        iFileColumnWidth = max(iFileColumnWidth, len(sFile))
    if total_width_exceeds_report_width(iFileColumnWidth):
        iFileColumnWidth = MAXIMUM_FILENAME_COLUMN_WIDTH
    return iFileColumnWidth


def total_width_exceeds_report_width(iFileColumnWidth):
    return iFileColumnWidth > MAXIMUM_FILENAME_COLUMN_WIDTH


def build_md5sum_table_rows(lFiles):
    lLines = []
    for sFile in lFiles:
        sMd5sum = generate_md5sum(sFile)
        lLines.append(sMd5sum + ' '*COLUMN_GAP + sFile)
    return lLines


def generate_md5sum(sFilename):
    with open(sFilename, 'rb') as oFile:
        return hashlib.file_digest(oFile, 'md5').hexdigest()


def build_section_3(oPortResults):
    lLines = []
    lLines.extend(build_section_3_header())
    for iPortResult, oPortResult in enumerate(oPortResults.results, start=1):
        lLines.append('')
        lLines.extend(build_port_results_section(iPortResult, oPortResult))
    return lLines


def build_section_3_header():
    lLines = []
    lLines.append(build_major_divider())
    lLines.append('Section 3: Port Rule Checks')
    lLines.append(build_major_divider())
    return lLines


def build_port_results_section(iPortResult, oPortResult):
    lLines = []
    lLines.extend(build_port_results_header(iPortResult, oPortResult))
    iRuleIdColumnWidth = get_max_rule_id_column_width(oPortResult)
    lLines.append(build_port_rule_check_header(iRuleIdColumnWidth))
    for oStageResult in oPortResult.methodology_results.stage_results:
        lLines.extend(build_stage_result_rows(iRuleIdColumnWidth, oStageResult))
    lLines.append(build_minor_divider())
    return lLines


def build_port_results_header(iPortResult, oPortResult):
    sRuleKey = build_report_key(oPortResult)
    lLines = []
    lLines.append(build_minor_divider())
    lLines.append(f'Section 3.{iPortResult}: {sRuleKey} Rule Checks')
    lLines.append(build_minor_divider())
    return lLines


def get_max_rule_id_column_width(oPortResult):
    iMaxWidth = 0
    for oStageResult in oPortResult.methodology_results.stage_results:
        for oRuleResult in oStageResult.rule_results.results:
            iMaxWidth = max(iMaxWidth, len(oRuleResult.rule_id))
    return iMaxWidth


def build_port_rule_check_header(iRuleIdColumnWidth):
    sHeader = f'{"Rule":<{iRuleIdColumnWidth}}'
    sHeader += ' '*COLUMN_GAP
    sHeader += f'{"Result":<{RESULT_COLUMN_WIDTH}}'
    sHeader += ' '*COLUMN_GAP
    sHeader += 'Details'
    return sHeader


def build_stage_result_rows(iRuleIdColumnWidth, oStageResult):
    lLines = []
    lLines.append(build_stage_separator(oStageResult))
    lLines.extend(build_stage_rule_results(iRuleIdColumnWidth, oStageResult))
    return lLines


def build_stage_separator(oStageResult):
    sLine = '- ' + oStageResult.name + ' '
    sLine = sLine + '-' * (REPORT_WIDTH - len(sLine))
    return sLine


def build_stage_rule_results(iRuleIdColumnWidth, oStageResult):
    lLines = []
    for oResult in oStageResult.rule_results.results:
        if result_has_detail(oResult):
            lLines.extend(build_result_with_detail(iRuleIdColumnWidth, oResult))
        else:
            lLines.append(build_result_without_detail(iRuleIdColumnWidth, oResult))
    return lLines


def result_has_detail(oResult):
    return len(oResult.details) > 0


def build_result_without_detail(iRuleIdColumnWidth, oResult):
    sRuleId = oResult.rule_id
    sResult = oResult.status.capitalize()
    sLine = f'{sRuleId:{iRuleIdColumnWidth}}'
    sLine += ' '*COLUMN_GAP
    sLine += f'{sResult:{RESULT_COLUMN_WIDTH}}'
    return sLine.rstrip()


def build_result_with_detail(iRuleIdColumnWidth, oResult):
    lLines = []
    sRuleId = oResult.rule_id
    sResult = oResult.status.capitalize()
    for sDetail in oResult.details:
        sLine = f'{sRuleId:{iRuleIdColumnWidth}}'
        sLine += ' '*COLUMN_GAP
        sLine += f'{sResult:{RESULT_COLUMN_WIDTH}}'
        sLine += ' '*COLUMN_GAP
        sLine += sDetail
        lLines.append(sLine.rstrip())
        sRuleId = ''
        sResult = ''
    return lLines
