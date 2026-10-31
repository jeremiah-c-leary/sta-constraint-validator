from stacv.interface import interface_config
from stacv.generate import xdc_file
from stacv.part import part
from stacv.traces import traces


def execute(oCmdLine):
    oInterface = interface_config.read_interface_config(oCmdLine.interface_file)
    oTraceList = traces.create_trace_list(oInterface)
    oPart = part.create_part(oInterface)
    for sLine in xdc_file.generate_file(oInterface, oTraceList, oPart):
        print(sLine)
    return 0
