import sys

from . import cmd_line_args
from . import subcommand


def main():
    '''
    Main routine of the STA Constraint Validator program.
    '''

    command_line_arguments = cmd_line_args.parse_command_line_arguments()

    if command_line_arguments.which == 'debug':
        subcommand.debug.execute(command_line_arguments)
