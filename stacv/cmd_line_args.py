
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
    build_debug_subparser(subparsers)
    build_version_parser(subparsers)

    args = top_parser.parse_args()

    print_help_if_no_command_line_options_given(top_parser)

    return args


def add_file_arguments_to_parser(parser):
    parser.add_argument('config_file', help='Configuration files.')


def build_report_subparser(subparser):
    parser = subparser.add_parser('report', help='Generate reports')
    parser.add_argument('analysis_report', help='Output analysis file')
    add_file_arguments_to_parser(parser)

    parser.set_defaults(which='report')


def build_debug_subparser(subparser):
    parser = subparser.add_parser('debug', help='Alpha debug reporting.')
    add_file_arguments_to_parser(parser)
    parser.add_argument('output', default=None, action='store', choices=['text_block_diagram', 'text_clock_diagram'], help='Output text version of the block diagram')

    parser.set_defaults(which='debug')


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
