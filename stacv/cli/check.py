
from stacv.interface import interface_config
from stacv.inputs import port_profile
from stacv.methodology import methodology_factory
from stacv.output import check_report
from stacv.output import junit
from stacv.part import part
from stacv.results import port_result
from stacv.results import port_result_list
from stacv.timing_report import timing_report_file
from stacv.timing_report import timing_report_list
from stacv.timing_report.xilinx import vivado
from stacv.traces import traces


def execute(oCmdLine, oDateTime, lArgv):
    print(f'Reading interface file {oCmdLine.interface_file}')
    oInterface = interface_config.read_interface_config(oCmdLine.interface_file)
    interface_config.check_timing_reports_exist(oInterface, oCmdLine.interface_file)
    oPortResults = get_port_results(oInterface)
    if oCmdLine.report is not None:
        check_report.write_check_report(oCmdLine.report, oDateTime, lArgv, oInterface, oPortResults, oCmdLine.interface_file)
    if oCmdLine.junit is not None:
        junit.generate_junit_file(oCmdLine.junit, oPortResults)
    if oPortResults.has_failures():
        return 1
    print('Check Passed')
    return 0


def get_port_results(oInterface):
    oPortResults = port_result_list.PortResultList()
    oTraceList = traces.create_trace_list(oInterface)
    oPart = part.create_part(oInterface)
    for oPort in oInterface.ports:
        oPortResult = get_port_result(oPort, oTraceList, oPart)
        oPortResults.add_result(oPortResult)
    return oPortResults


def get_port_result(oPort, oTraceList, oPart):
    oTimingReports = create_timing_reports(oPort.timing_reports)
    oPortProfile = port_profile.PortProfile(oPort, oTraceList, oPart, oTimingReports)
    oMethodology = create_methodology(oPort)
    oMethodologyResults = oMethodology.check(oPortProfile)
    print_failing_rules(oMethodologyResults)
    return port_result.PortResult(oPort, oMethodologyResults)


def create_methodology(oPort):
    return methodology_factory.create_methodology(oPort.methodology)


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


def print_failing_rules(oMethodologyResults):
    for oRuleResult in oMethodologyResults.get_failing_results():
        print(f'FAILED: [{oRuleResult.rule_id}]')
