
import os

from stacv import version
from stacv.config import interface_config
from stacv.methodology import methodology_factory
from stacv.timing_report import timing_report_file
from stacv.timing_report import timing_report_list
from stacv.timing_report.xilinx import vivado


def execute(oCmdLine, oDateTime, lArgv):
    print(f'Reading configuration file {oCmdLine.config_file}')
    oInterface = interface_config.read_interface_config(oCmdLine.config_file)
    bFailures = interface_has_failures(oInterface)
    if oCmdLine.report is not None:
        write_check_report(oCmdLine.report, oDateTime, lArgv)
    if bFailures:
        return 1
    return 0


def interface_has_failures(oInterface):
    bFailures = False
    for oPort in oInterface.ports:
        if port_has_failures(oPort):
            bFailures = True
    return bFailures


def port_has_failures(oPort):
    oMethodology = create_methodology(oPort)
    oTimingReportList = create_timing_reports(oPort.timing_reports)
    oMethodologyResults = oMethodology.check(oTimingReportList)
    print_failing_rules(oMethodologyResults)
    return oMethodologyResults.has_failures()


def create_methodology(oPort):
    return methodology_factory.create_methodology(oPort.methodology)


def print_failing_rules(oRuleResults):
    for oRuleResult in oRuleResults.get_failing_results():
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


def write_check_report(sFilename, oDateTime, lArgv):
    print(f'Creating report {sFilename}')
    lLines = []
    lLines.extend(build_header(oDateTime, lArgv))
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


def write_file(sFilename, lLines):
    with open(sFilename, 'w') as oFile:
        oFile.write('\n'.join(lLines) + '\n')
