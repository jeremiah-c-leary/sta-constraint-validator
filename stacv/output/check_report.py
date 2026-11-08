
import os

from stacv import version
from stacv.output import md5sum_table
from stacv.output import text_table
from stacv.results import port_result


REPORT_WIDTH = 80
COLUMN_GAP = 2
SUMMARY_COLUMN_GAP = 3
RESULT_COLUMN_WIDTH = len('Skipped')


def write_check_report(sFilename, oDateTime, lArgv, oInterface, oPortResults, sInterfaceFile):
    print(f'Creating report {sFilename}')
    lLines = []
    lLines.extend(build_header(oDateTime, lArgv))
    lLines.append('')
    lLines.extend(build_table_of_contents(oPortResults))
    lLines.append('')
    lLines.extend(build_section_1(oInterface, oPortResults))
    lLines.append('')
    lLines.extend(build_section_2(oPortResults, sInterfaceFile))
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


def build_table_of_contents(oPortResults):
    lLines = []
    lLines.append('Table of Contents')
    lLines.append('')
    lLines.append(build_section_1_title())
    lLines.append(build_section_2_title())
    lLines.append(build_section_3_title())
    for iPortResult, oPortResult in enumerate(get_analyzed_port_results(oPortResults), start=1):
        lLines.append(build_section_3_port_title(iPortResult, oPortResult))
    return lLines


def get_analyzed_port_results(oPortResults):
    # Deferred ports have no rule checks, so only analyzed ports get a section.
    lPortResults = []
    for oPortResult in oPortResults.results:
        if not oPortResult.is_deferred():
            lPortResults.append(oPortResult)
    return lPortResults


def build_section_1_title():
    return 'Section 1: Summary'


def build_section_2_title():
    return 'Section 2: Inputs'


def build_section_3_title():
    return 'Section 3: Port Rule Checks'


def build_section_3_port_title(iPortResult, oPortResult):
    sSectionNumber = build_port_section_number(iPortResult)
    sReportKey = oPortResult.get_identifier()
    return f'Section {sSectionNumber}: {sReportKey} Rule Checks'


def build_port_section_number(iNumber):
    return f'3.{iNumber}'


def build_section_1(oInterface, oPortResults):
    lLines = []
    lLines.append(build_major_divider())
    lLines.append(build_section_1_title())
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
    return text_table.format_table(lRows, SUMMARY_COLUMN_GAP)


def build_unformatted_table(oPortResults):
    lTable = []
    lTable.append(['Port', 'Methodology', 'Report Key', 'Section', 'Result', 'Setup Slack', 'Hold Slack'])
    iPortResult = 0
    for oPortResult in oPortResults.results:
        if oPortResult.is_deferred():
            lTable.append(build_deferred_row(oPortResult))
        else:
            iPortResult += 1
            lTable.append(build_analyzed_row(iPortResult, oPortResult))
    return lTable


def build_deferred_row(oPortResult):
    return [oPortResult.port.name, oPortResult.get_methodology(), oPortResult.get_identifier(), '-', 'Deferred', '-', '-']


def build_analyzed_row(iPortResult, oPortResult):
    lRow = [oPortResult.port.name]
    lRow.append(oPortResult.port.methodology)
    lRow.append(oPortResult.get_identifier())
    lRow.append(build_port_section_number(iPortResult))
    if oPortResult.has_failures():
        lRow.extend(['Failed', '-', '-'])
    else:
        lRow.append('Passed')
        lRow.append(format_slack_cell(oPortResult.setup_slack))
        lRow.append(format_slack_cell(oPortResult.hold_slack))
    return lRow


def format_slack_cell(fSlack):
    # A failed port's slack is not shown, as a failing rule can mean the timing tool's slack is wrong.
    if fSlack is None:
        return '-'
    return port_result.format_slack(fSlack)


def build_section_2(oPortResults, sInterfaceFile):
    lLines = []
    lLines.extend(build_section_2_header())
    lLines.append('')
    lLines.extend(build_section_2_table(oPortResults, sInterfaceFile))
    return lLines


def build_section_2_header():
    lLines = []
    lLines.append(build_major_divider())
    lLines.append(build_section_2_title())
    lLines.append(build_major_divider())
    return lLines


def build_section_2_table(oPortResults, sInterfaceFile):
    lFiles = get_input_filenames(oPortResults, sInterfaceFile)
    return md5sum_table.build_md5sum_table(lFiles)


def get_input_filenames(oPortResults, sInterfaceFile):
    lFiles = []
    lFiles.append(sInterfaceFile)
    lFiles.extend(get_unique_timing_report_filenames(oPortResults))
    return lFiles


def get_unique_timing_report_filenames(oPortResults):
    lFilenames = []
    for oPortResult in oPortResults.results:
        for sFilename in oPortResult.port.timing_reports:
            if sFilename not in lFilenames:
                lFilenames.append(sFilename)
    return lFilenames


def build_section_3(oPortResults):
    lLines = []
    lLines.extend(build_section_3_header())
    for iPortResult, oPortResult in enumerate(get_analyzed_port_results(oPortResults), start=1):
        lLines.append('')
        lLines.extend(build_section_3_port(iPortResult, oPortResult))
    return lLines


def build_section_3_header():
    lLines = []
    lLines.append(build_major_divider())
    lLines.append(build_section_3_title())
    lLines.append(build_major_divider())
    return lLines


def build_section_3_port(iPortResult, oPortResult):
    lLines = []
    lLines.extend(build_section_3_port_header(iPortResult, oPortResult))
    iRuleIdColumnWidth = get_max_rule_id_column_width(oPortResult)
    lLines.append(build_section_3_result_row(iRuleIdColumnWidth, 'Rule', 'Result', 'Details'))
    for oStageResult in oPortResult.methodology_results.stage_results:
        lLines.extend(build_stage_lines(iRuleIdColumnWidth, oStageResult))
    lLines.append(build_minor_divider())
    return lLines


def build_section_3_port_header(iPortResult, oPortResult):
    lLines = []
    lLines.append(build_minor_divider())
    lLines.append(build_section_3_port_title(iPortResult, oPortResult))
    lLines.append(build_minor_divider())
    return lLines


def get_max_rule_id_column_width(oPortResult):
    iMaxWidth = len('Rule')
    for oRuleResult in oPortResult.get_results().results:
        iMaxWidth = max(iMaxWidth, len(oRuleResult.rule_id))
    return iMaxWidth


def build_section_3_result_row(iRuleIdColumnWidth, sRuleId, sResult, sDetail=''):
    sLine = f'{sRuleId:<{iRuleIdColumnWidth}}'
    sLine += ' '*COLUMN_GAP
    sLine += f'{sResult:<{RESULT_COLUMN_WIDTH}}'
    sLine += ' '*COLUMN_GAP
    sLine += sDetail
    return sLine.rstrip()


def build_stage_lines(iRuleIdColumnWidth, oStageResult):
    lLines = []
    lLines.append(build_stage_separator(oStageResult))
    lLines.extend(build_rule_lines(iRuleIdColumnWidth, oStageResult))
    return lLines


def build_stage_separator(oStageResult):
    sLine = '- ' + oStageResult.name + ' '
    sLine = sLine + '-' * (REPORT_WIDTH - len(sLine))
    return sLine


def build_rule_lines(iRuleIdColumnWidth, oStageResult):
    lLines = []
    for oResult in oStageResult.get_results().results:
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
    return build_section_3_result_row(iRuleIdColumnWidth, sRuleId, sResult)


def build_result_with_detail(iRuleIdColumnWidth, oResult):
    lLines = []
    sRuleId = oResult.rule_id
    sResult = oResult.status.capitalize()
    for sDetail in oResult.details:
        sLine = build_section_3_result_row(iRuleIdColumnWidth, sRuleId, sResult, sDetail)
        lLines.append(sLine)
        sRuleId = ''
        sResult = ''
    return lLines


def write_file(sFilename, lLines):
    with open(sFilename, 'w') as oFile:
        oFile.write('\n'.join(lLines) + '\n')
