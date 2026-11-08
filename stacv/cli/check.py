
import os

from stacv.interface import interface_config
from stacv.interface import part_coverage
from stacv.interface import port
from stacv.inputs import port_profile
from stacv.methodology import methodology_factory
from stacv.output import check_report
from stacv.output import junit
from stacv.part import part
from stacv.results import deferred_port_result
from stacv.results import port_result
from stacv.results import port_result_list
from stacv.standards import interface_standard
from stacv.timing_report import timing_report_file
from stacv.timing_report import timing_report_list
from stacv.timing_report.xilinx import vivado
from stacv.traces import traces


def execute(oCmdLine, oDateTime, lArgv):
    print(f'Reading interface file {build_console_path(oCmdLine.interface_file)}')
    oInterface = interface_config.read_interface_config(oCmdLine.interface_file)
    interface_config.resolve_timing_reports(oInterface, oCmdLine.interface_file)
    oPortResults = get_port_results(oCmdLine.interface_file, oInterface)
    if oCmdLine.report is not None:
        check_report.write_check_report(oCmdLine.report, oDateTime, lArgv, oInterface, oPortResults, oCmdLine.interface_file)
    if oCmdLine.junit is not None:
        junit.generate_junit_file(oCmdLine.junit, oPortResults)
    if oPortResults.has_failures():
        return 1
    print('Check Passed')
    return 0


def get_port_results(sInterfaceFile, oInterface):
    oPortResults = port_result_list.PortResultList()
    oTraceList = traces.create_trace_list(oInterface)
    oPart = part.create_part(oInterface)
    interface_standard.link_and_check(sInterfaceFile, oInterface, oTraceList, oPart)
    part_coverage.check_every_part_pin_has_a_port(sInterfaceFile, oInterface, oTraceList, oPart)
    for oPort in oInterface.ports:
        oPortResult = get_port_result(oPort, oTraceList, oPart)
        oPortResults.add_result(oPortResult)
    return oPortResults


def get_port_result(oPort, oTraceList, oPart):
    if not interface_config.is_checked(oPort):
        oDeferredPortResult = deferred_port_result.DeferredPortResult(oPort)
        print(f'DEFERRED: {oDeferredPortResult.get_identifier()}')
        return oDeferredPortResult
    oTimingReports = create_timing_reports(oPort.timing_reports)
    oPortProfile = port_profile.PortProfile(oPort, oTraceList, oPart, oTimingReports)
    oMethodology = create_methodology(oPort)
    oMethodologyResults = oMethodology.check(oPortProfile)
    oPortResult = port_result.PortResult(oPort, oMethodologyResults)
    oPortResult.setup_slack = find_worst_slack(oTimingReports.get_setup_reports())
    oPortResult.hold_slack = find_worst_slack(oTimingReports.get_hold_reports())
    print_port_result(oPortResult, oPort.timing_reports)
    return oPortResult


def find_worst_slack(lTimingReports):
    fWorstSlack = None
    for oTimingReport in lTimingReports:
        if fWorstSlack is None or oTimingReport.slack < fWorstSlack:
            fWorstSlack = oTimingReport.slack
    return fWorstSlack


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
    print(f'Reading timing report file {build_console_path(sTimingReport)}')
    lLines = read_text_file(sTimingReport)
    return timing_report_file.TimingReportFile(sTimingReport, lLines)


def read_text_file(sFilename):
    with open(sFilename, 'r') as oFile:
        return oFile.readlines()


def parse_timing_report(oTimingReportFile):
    return vivado.parse_timing_report(oTimingReportFile)


def merge_timing_reports(oTimingReportList, oParsedTimingReportList):
    oTimingReportList.extend(oParsedTimingReportList)


def print_port_result(oPortResult, lTimingReports):
    oMethodologyResults = oPortResult.methodology_results
    if not oMethodologyResults.has_failures():
        print(build_passed_line(oPortResult))
        return
    for oRuleResult in oMethodologyResults.get_failing_results():
        print(f'FAILED: [{oRuleResult.rule_id}] {oPortResult.get_identifier()}')
        print_details(oRuleResult.details, lTimingReports)


def build_passed_line(oPortResult):
    sLine = f'PASSED: {oPortResult.get_identifier()}'
    sSlack = oPortResult.describe_slack()
    if sSlack == '':
        return sLine
    return f'{sLine}  {sSlack}'


def print_details(lDetails, lTimingReports):
    for sDetail in lDetails:
        print(f'    {build_console_detail(sDetail, lTimingReports)}')


def build_console_detail(sDetail, lTimingReports):
    # A detail starts with the timing report it is in, which the console shows relative to where stacv runs.
    for sTimingReport in lTimingReports:
        if sDetail.startswith(sTimingReport + ':'):
            return build_console_path(sTimingReport) + sDetail[len(sTimingReport):]
    return sDetail


def build_console_path(sFilename):
    # The console is read where stacv runs, so paths are shortened; the report file keeps them as written.
    return os.path.relpath(sFilename)
