import sys

from stacv.cli import cmd_line_args
from stacv.cli import check
from stacv.config import interface_config_error
from stacv.timing_report import timing_report_parse_error


def main():
    '''
    Main routine of the STA Constraint Validator program.
    '''

    command_line_arguments = cmd_line_args.parse_command_line_arguments()

    if command_line_arguments.which == 'check':
        try:
            iExitCode = check.execute(command_line_arguments)
        except interface_config_error.InterfaceConfigError as oError:
            iExitCode = 2
            print(str(oError), file=sys.stderr)
        except timing_report_parse_error.TimingReportParseError as oError:
            iExitCode = 2
            print(str(oError), file=sys.stderr)
        
        sys.exit(iExitCode)
