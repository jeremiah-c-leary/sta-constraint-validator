from stacv.interface import interface_config
from stacv.part import part
from stacv.traces import traces
from stacv.visualize import block_diagram
from stacv.visualize import edges

DIVIDER = '=' * 80


def execute(oCmdLine):
    oInterface = interface_config.read_interface_config(oCmdLine.interface_file)
    if oCmdLine.visualization == 'block_diagram':
        print_block_diagram(oInterface)
        return 0
    for oPort in oInterface.ports:
        print_port_edges(oPort)
    return 0


def print_block_diagram(oInterface):
    oTraceList = traces.create_trace_list(oInterface)
    oPart = part.create_part(oInterface)
    for sLine in block_diagram.draw_block_diagram(oInterface, oTraceList, oPart):
        print(sLine)


def print_port_edges(oPort):
    print(DIVIDER)
    print(f'Port:  {oPort.name}')
    print(DIVIDER)
    print('')
    for sLine in edges.draw_edges(oPort):
        print(sLine)
    print('')
