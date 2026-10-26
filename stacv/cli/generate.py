from stacv.interface import interface_config
from stacv.generate import xdc


def execute(oCmdLine):
    oInterface = interface_config.read_interface_config(oCmdLine.interface_file)
    for sLine in xdc.generate_constraints(oInterface):
        print(sLine)
    return 0
