from stacv.interface import interface_config
from stacv.generate import xdc_file
from stacv.part import part
from stacv.traces import traces


def execute(oCmdLine):
    oInterface = interface_config.read_interface_config(oCmdLine.interface_file)
    oTraceList = traces.create_trace_list(oInterface)
    oPart = part.create_part(oInterface)
    lLines = xdc_file.generate_file(oCmdLine.interface_file, oInterface, oTraceList, oPart)
    if oCmdLine.output is None:
        print_lines(lLines)
    else:
        write_file(oCmdLine.output, lLines)
    return 0


def print_lines(lLines):
    for sLine in lLines:
        print(sLine)


def write_file(sFilename, lLines):
    print(f'Creating XDC file {sFilename}')
    with open(sFilename, 'w') as oFile:
        for sLine in lLines:
            oFile.write(sLine + '\n')
