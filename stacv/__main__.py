import sys

from . import cmd_line_args


def main():
    '''
    Main routine of the STA Constraint Validator program.
    '''

    commandLineArguments = cmd_line_args.parse_command_line_arguments()

