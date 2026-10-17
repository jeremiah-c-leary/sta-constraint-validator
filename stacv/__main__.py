import sys

from stacv.cli import cmd_line_args
from stacv.cli import check


def main():
    '''
    Main routine of the STA Constraint Validator program.
    '''

    iExitCode = 0
    command_line_arguments = cmd_line_args.parse_command_line_arguments()

    if command_line_arguments.which == 'check':
        iExitCode = check.execute(command_line_arguments)

    sys.exit(iExitCode)
