import datetime
import sys

from stacv.cli import cmd_line_args
from stacv.cli import check
from stacv.cli import generate
from stacv.cli import visualize
from stacv.generate import generate_error
from stacv.interface import interface_config_error
from stacv.timing_report import timing_report_parse_error
from stacv.traces import traces_config_error


def main():
    '''
    Main routine of the STA Constraint Validator program.
    '''

    command_line_arguments = cmd_line_args.parse_command_line_arguments()

    if command_line_arguments.which == 'check':
        try:
            iExitCode = check.execute(command_line_arguments, datetime.datetime.now(), sys.argv)
        except interface_config_error.InterfaceConfigError as oError:
            iExitCode = 2
            print(str(oError), file=sys.stderr)
        except traces_config_error.TracesConfigError as oError:
            iExitCode = 2
            print(str(oError), file=sys.stderr)
        except timing_report_parse_error.TimingReportParseError as oError:
            iExitCode = 2
            print(str(oError), file=sys.stderr)
        
        sys.exit(iExitCode)

    if command_line_arguments.which == 'visualize':
        try:
            iExitCode = visualize.execute(command_line_arguments)
        except interface_config_error.InterfaceConfigError as oError:
            iExitCode = 2
            print(str(oError), file=sys.stderr)
        except traces_config_error.TracesConfigError as oError:
            iExitCode = 2
            print(str(oError), file=sys.stderr)

        sys.exit(iExitCode)

    if command_line_arguments.which == 'generate':
        try:
            iExitCode = generate.execute(command_line_arguments)
        except interface_config_error.InterfaceConfigError as oError:
            iExitCode = 2
            print(str(oError), file=sys.stderr)
        except traces_config_error.TracesConfigError as oError:
            iExitCode = 2
            print(str(oError), file=sys.stderr)
        except generate_error.GenerateError as oError:
            iExitCode = 2
            print(str(oError), file=sys.stderr)

        sys.exit(iExitCode)
