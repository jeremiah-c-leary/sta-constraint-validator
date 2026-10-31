from stacv.interface import interface_config
from stacv.generate import report_tcl_file
from stacv.generate import xdc_file
from stacv.part import part
from stacv.traces import traces


def execute(oCmdLine, lArgv):
    oInterface = interface_config.read_interface_config(oCmdLine.interface_file)
    if oCmdLine.target == 'report_tcl':
        lLines = report_tcl_file.generate_file(oCmdLine.interface_file, oInterface, lArgv)
        write_output(oCmdLine.output, lLines, 'report script')
        return 0
    lLines = generate_xdc_file(oCmdLine.interface_file, oInterface)
    write_output(oCmdLine.output, lLines, 'XDC file')
    return 0


def generate_xdc_file(sInterfaceFile, oInterface):
    oTraceList = traces.create_trace_list(oInterface)
    oPart = part.create_part(oInterface)
    return xdc_file.generate_file(sInterfaceFile, oInterface, oTraceList, oPart)


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
