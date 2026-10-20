
import hashlib
import os

from stacv import version
from stacv.output import check_report
from stacv.output import junit
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
        check_report.write_check_report(oCmdLine.report, oDateTime, lArgv, oInterface, oPortResults, oCmdLine.config_file)
    if oCmdLine.junit is not None:
        junit.generate_junit_file(oCmdLine.junit, oPortResults)
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
