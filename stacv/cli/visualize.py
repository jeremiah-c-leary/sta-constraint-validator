from stacv.interface import interface_config
from stacv.visualize import edges

DIVIDER = '=' * 80


def execute(oCmdLine):
    oInterface = interface_config.read_interface_config(oCmdLine.interface_file)
    for oPort in oInterface.ports:
        print_port_edges(oPort)
    return 0


def print_port_edges(oPort):
    print(DIVIDER)
    print(f'Port:  {oPort.name}')
    print(DIVIDER)
    print('')
    for sLine in edges.draw_edges(oPort):
        print(sLine)
    print('')
