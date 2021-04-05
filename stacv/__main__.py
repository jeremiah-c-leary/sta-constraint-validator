
from . import cmd_line_args
from stacv.subcommand import debug


def main():
    '''
    Main routine of the STA Constraint Validator program.
    '''

    command_line_arguments = cmd_line_args.parse_command_line_arguments()

    if command_line_arguments.which == 'debug':
        debug.execute(command_line_arguments)
