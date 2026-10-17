
import argparse
import sys

PROGRAM = 'stacv'


def parse_command_line_arguments():
    '''
    Parses the command line arguments and returns them.
    '''
    top_parser = create_top_parser()

    add_subparsers(top_parser)

    args = top_parser.parse_args()

    print_help_if_no_command_line_options_given(top_parser)

    return args


def create_top_parser():
    top_parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description='''Validates timing constraints.'''
        )
    return top_parser


def add_subparsers(top_parser):
    subparsers = top_parser.add_subparsers()

    build_check_subparser(subparsers)


def build_check_subparser(subparser):
    parser = subparser.add_parser('check', help='Perform Timing Rule Checks on timing reports.')
    parser.add_argument('config_file', help='Configuration files.')
    parser.set_defaults(which='check')


def print_help_if_no_command_line_options_given(parser):
    '''
    Will print the help output if no command line arguments were given.
    '''
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(2)
