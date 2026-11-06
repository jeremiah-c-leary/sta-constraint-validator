import os

from stacv.interface import interface_config
from stacv.interface import part_coverage
from stacv.generate import datasheet_file
from stacv.generate import datasheet_pin
from stacv.generate import report_tcl_file
from stacv.generate import xdc_file
from stacv.part import part
from stacv.timing_report import timing_report_file
from stacv.timing_report.xilinx import vivado
from stacv.traces import traces


def execute(oCmdLine, lArgv):
    oInterface = interface_config.read_interface_config(oCmdLine.interface_file)
    if oCmdLine.target == 'report_tcl':
        lLines = report_tcl_file.generate_file(oCmdLine.interface_file, oInterface, lArgv)
        write_output(oCmdLine.output, lLines, 'report script')
        return 0
    if oCmdLine.target == 'datasheet':
        lLines = generate_datasheet_file(oCmdLine.interface_file, oInterface)
        write_output(oCmdLine.output, lLines, 'datasheet')
        return 0
    lLines = generate_xdc_file(oCmdLine.interface_file, oInterface)
    write_output(oCmdLine.output, lLines, 'XDC file')
    return 0


def generate_xdc_file(sInterfaceFile, oInterface):
    oTraceList = traces.create_trace_list(oInterface)
    oPart = part.create_part(oInterface)
    part_coverage.check_every_part_pin_has_a_port(sInterfaceFile, oInterface, oTraceList, oPart)
    return xdc_file.generate_file(sInterfaceFile, oInterface, oTraceList, oPart)


def generate_datasheet_file(sInterfaceFile, oInterface):
    # The datasheet is written from the timing reports, so it is generated after timing.
    interface_config.resolve_timing_reports(oInterface, sInterfaceFile)
    oInputs = datasheet_file.DatasheetInputs(sInterfaceFile, oInterface)
    for oPort in oInterface.get_analyzed_ports():
        if datasheet_pin.is_supported(oPort):
            oInputs.timing_reports[oPort.name] = read_timing_reports(oInputs, oPort.timing_reports)
    return datasheet_file.generate_file(oInputs)


def read_timing_reports(oInputs, lFilenames):
    oTimingReports = None
    for sFilename in lFilenames:
        with open(sFilename) as oFile:
            oTimingReportFile = timing_report_file.TimingReportFile(sFilename, oFile.readlines())
        if len(oInputs.header) == 0:
            oInputs.header = read_report_header(oTimingReportFile)
        oInputs.timing_report_files.append(os.path.relpath(sFilename))
        if oTimingReports is None:
            oTimingReports = vivado.parse_timing_report(oTimingReportFile)
        else:
            oTimingReports.extend(vivado.parse_timing_report(oTimingReportFile))
    return oTimingReports


def read_report_header(oTimingReportFile):
    # The header rows are written | Design       : dac81404_spi
    dHeader = {}
    for oLine in oTimingReportFile.lines:
        lParts = oLine.text.strip().lstrip('|').split(':', 1)
        sKey = lParts[0].strip()
        if len(lParts) == 2 and sKey in datasheet_file.HEADER_KEYS and sKey not in dHeader:
            dHeader[sKey] = lParts[1].strip()
    return dHeader


def write_output(sFilename, lLines, sDescription):
    if sFilename is None:
        print_lines(lLines)
    else:
        write_file(sFilename, lLines, sDescription)


def print_lines(lLines):
    for sLine in lLines:
        print(sLine)


def write_file(sFilename, lLines, sDescription):
    print(f'Creating {sDescription} {sFilename}')
    with open(sFilename, 'w') as oFile:
        for sLine in lLines:
            oFile.write(sLine + '\n')
