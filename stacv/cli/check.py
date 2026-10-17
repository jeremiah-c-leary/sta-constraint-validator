
from stacv.config import interface_config
from stacv.methodology import methodology_factory
from stacv.timing_report import timing_report_file
from stacv.timing_report import timing_report_list
from stacv.timing_report.xilinx import vivado


def execute(oCmdLine):
    oConfig = interface_config.read_interface_config(oCmdLine.config_file)
    if interfaces_have_failures(oConfig):
        return 1
    return 0


def interfaces_have_failures(oConfig):
    for oInterface in oConfig.interfaces:
        if ports_have_failures(oInterface):
            return True
    return False


def ports_have_failures(oInterface):
    for oPort in oInterface.ports:
        if timing_report_have_failures(oPort):
            return True
    return False


def timing_report_have_failures(oPort):
    oMethodology = create_methodology(oPort)
    oTimingReportList = create_timing_reports(oPort.timing_reports)
    oRuleResults = oMethodology.check(oTimingReportList)
    return oRuleResults.has_failures()


def create_methodology(oPort):
    return methodology_factory.create_methodology(oPort.methodology)


def create_timing_reportFile(sTimingReport):
    lLines = read_text_file(sTimingReport)
    return timing_report_file.TimingReportFile(sTimingReport, lLines)


def create_timing_reports(lFilenames):
    oTimingReportList = timing_report_list.TimingReportList()
    for sFilename in lFilenames:
        oTimingReportFile = create_timing_reportFile(sFilename)
        oParsedTimingReportList = parse_timing_report(oTimingReportFile)
        merge_timing_reports(oTimingReportList, oParsedTimingReportList)
    return oTimingReportList


def merge_timing_reports(oTimingReportList, oParsedTimingReportList):
    oTimingReportList.extend(oParsedTimingReportList)


def parse_timing_report(oTimingReportFile):
    return vivado.parse_timing_report(oTimingReportFile)


def read_text_file(sFilename):
    with open(sFilename, 'r') as oFile:
        return oFile.readlines()
