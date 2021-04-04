
import argparse
import sys

program = 'stacv'


def parse_command_line_arguments():
    '''
    Parses the command line arguments and returns them.
    '''
    top_parser = create_top_parser()

    subparsers = top_parser.add_subparsers()

    build_report_subparser(subparsers)
    build_version_parser(subparsers)

    args = top_parser.parse_args()

    print_help_if_no_command_line_options_given(top_parser)

    return args


def add_file_arguments_to_parser(parser):
    parser.add_argument('board_file', help='Board configuration data.')
    parser.add_argument('device_file', help='Device configuration data.')
    parser.add_argument('part_file', help='Part configuration data.')


def build_report_subparser(subparser):
    parser = subparser.add_parser('report', help='Generate reports')
    add_file_arguments_to_parser(parser)
    parser.add_argument('analysis_report', help='Output analysis file')

    parser.set_defaults(which='report')


def build_version_parser(subparser):
    parser = subparser.add_parser('version', help=f'Displays {program.upper()} version information')

    parser.set_defaults(which='version')


def create_top_parser():
    top_parser = argparse.ArgumentParser(
        prog=program,
        description='''Validates timing constraints.'''
        )
    return top_parser


def print_help_if_no_command_line_options_given(parser):
    '''
    Will print the help output if no command line arguments were given.
    '''
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)