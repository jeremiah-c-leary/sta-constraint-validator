from stacv.interface import interface_config
from stacv.interface import part_coverage
from stacv.methodology import methodology_factory
from stacv.part import part
from stacv.traces import traces
from stacv.visualize import block_diagram
from stacv.visualize import edges

DIVIDER = '=' * 80


def execute(oCmdLine):
    if oCmdLine.visualization == 'block_diagram':
        print_block_diagram(oCmdLine.interface_file, interface_config.read_interface_config(oCmdLine.interface_file))
        return 0
    return print_interface_edges(interface_config.read_interface_config_for_drawing(oCmdLine.interface_file))


def print_interface_edges(oInterface):
    # The edges are drawn even when they are wrong, so the drawing can be used to correct them.
    iExitCode = 0
    for oPort in oInterface.get_analyzed_ports():
        print_port_edges(oPort)
        if len(oPort.edge_errors) > 0:
            iExitCode = 2
    return iExitCode


def print_block_diagram(sInterfaceFile, oInterface):
    oTraceList = traces.create_trace_list(oInterface)
    oPart = part.create_part(oInterface)
    part_coverage.check_every_part_pin_has_a_port(sInterfaceFile, oInterface, oTraceList, oPart)
    for sLine in block_diagram.draw_block_diagram(oInterface, oTraceList, oPart):
        print(sLine)


def print_port_edges(oPort):
    print(DIVIDER)
    print(f'Port:  {oPort.name}')
    print(DIVIDER)
    print('')
    oMethodology = methodology_factory.create_methodology(oPort.methodology)
    for sLine in edges.draw_edges(oPort, oMethodology.edge_diagram_type):
        print(sLine)
    print_edge_errors(oPort)
    print('')


def print_edge_errors(oPort):
    if len(oPort.edge_errors) == 0:
        return
    print('')
    for oError in oPort.edge_errors:
        print(str(oError))
