
from stacv.config import interface_config
from stacv.methodology import methodology_factory
from stacv.timing_report import timing_report_file
from stacv.timing_report import timing_report_list
from stacv.timing_report.xilinx import vivado


def check_interfaces(oConfig):
    for oInterface in oConfig.interfaces:
        if check_ports(oInterface):
            return 1
    return 0


def create_methodology(oPort):
    return methodology_factory.create_methodology(oPort.methodology)


def check_ports(oInterface):
    for oPort in oInterface.ports:
        if check_timing_reports(oPort):
            return 1
    return 0


def check_timing_reports(oPort):
    oMethodology = create_methodology(oPort)
    oTimingReportList = create_timing_reports(oPort.timing_reports)
    oRuleResults = oMethodology.check(oTimingReportList)
    return oRuleResults.has_failures()


def create_timing_report(sTimingReport):
    lTimingReportFile = read_text_file(sTimingReport)
    return timing_report_file.TimingReportFile(sTimingReport, lTimingReportFile)


def create_timing_reports(lTimingReports):
    oTimingReportList = timing_report_list.TimingReportList()
    for sTimingReport in lTimingReports:
        oTimingReport = create_timing_report(sTimingReport)
        oParsedTimingReportList = parse_timing_report(oTimingReport)
        merge_timing_reports(oTimingReportList, oParsedTimingReportList)
    return oTimingReportList


def execute(oCmdLine):
    oConfig = interface_config.read_interface_config(oCmdLine.config_file)
    return check_interfaces(oConfig)


def merge_timing_reports(oTimingReportList, oParsedTimingReportList):
    oTimingReportList.extend(oParsedTimingReportList)


def parse_timing_report(oTimingReportFile):
    return vivado.parse_timing_report(oTimingReportFile)


def read_text_file(sFilename):
    with open(sFilename, 'r') as oFile:
        return oFile.readlines()
