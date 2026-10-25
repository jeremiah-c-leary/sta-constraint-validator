from stacv.interface import interface_config


def execute(oCmdLine):
    oInterface = interface_config.read_interface_config(oCmdLine.interface_file)
    return 0
