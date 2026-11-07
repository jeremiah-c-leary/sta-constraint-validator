
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


class HelpfulArgumentParser(argparse.ArgumentParser):
    '''
    Prints the help of the command before a usage error, so the user can see
    which words and arguments the command takes.  Subcommands use the same class.
    '''

    def error(self, message):
        self.print_help(sys.stderr)
        sys.stderr.write('\n')
        self.exit(2, f'{self.prog}: error: {message}\n')


def create_top_parser():
    top_parser = HelpfulArgumentParser(
        prog=PROGRAM,
        description='''Validates timing constraints.'''
        )
    return top_parser


def add_subparsers(top_parser):
    subparsers = top_parser.add_subparsers()

    build_check_subparser(subparsers)
    build_visualize_subparser(subparsers)
    build_generate_subparser(subparsers)
    build_create_subparser(subparsers)


def build_check_subparser(subparser):
    parser = subparser.add_parser('check', help='Perform Timing Rule Checks on timing reports.')
    parser.add_argument('interface_file', help='Interface TOML file.')
    parser.add_argument('--report', help='Check report file name.')
    parser.add_argument('--junit', help='Generate a JUnit file.')
    parser.set_defaults(which='check')


def build_visualize_subparser(subparser):
    parser = subparser.add_parser('visualize', help='Draw what the interface file intends to time.')
    parser.set_defaults(which='visualize')
    visualizations = parser.add_subparsers(dest='visualization', required=True)
    build_edges_subparser(visualizations)
    build_block_diagram_subparser(visualizations)
    build_eye_subparser(visualizations)


def build_edges_subparser(subparser):
    parser = subparser.add_parser('edges', help='Draw the launch and capture clock edges of every port.')
    parser.add_argument('interface_file', help='Interface TOML file.')


def build_block_diagram_subparser(subparser):
    parser = subparser.add_parser('block_diagram', help='Draw the device, the part and the traces between them.')
    parser.add_argument('interface_file', help='Interface TOML file.')


def build_eye_subparser(subparser):
    parser = subparser.add_parser('eye', help='Draw the eye of every port from its timing reports.')
    parser.add_argument('interface_file', help='Interface TOML file.')


def build_generate_subparser(subparser):
    parser = subparser.add_parser('generate', help='Generate Vivado files from the interface file.')
    parser.set_defaults(which='generate')
    targets = parser.add_subparsers(dest='target', required=True)
    build_xdc_subparser(targets)
    build_report_tcl_subparser(targets)
    build_datasheet_subparser(targets)


def build_xdc_subparser(subparser):
    parser = subparser.add_parser('xdc', help='Generate Vivado timing constraints for every port.')
    parser.add_argument('interface_file', help='Interface TOML file.')
    parser.add_argument('--output', help='Constraints file name.  The constraints are written to stdout without it.')


def build_report_tcl_subparser(subparser):
    parser = subparser.add_parser('report_tcl', help='Generate a Vivado script that writes the timing reports of every analyzed port.')
    parser.add_argument('interface_file', help='Interface TOML file.')
    parser.add_argument('--output', help='Report script file name.  The script is written to stdout without it.')


def build_datasheet_subparser(subparser):
    parser = subparser.add_parser('datasheet', help='Generate the datasheet of the interface from its timing reports: the timing of each port at the device\'s pins.')
    parser.add_argument('interface_file', help='Interface TOML file.')
    parser.add_argument('--output', help='Datasheet file name.  The datasheet is written to stdout without it.')


def build_create_subparser(subparser):
    parser = subparser.add_parser('create', help='Create files to start an interface from.')
    parser.set_defaults(which='create')
    targets = parser.add_subparsers(dest='target', required=True)
    build_template_subparser(targets)


def build_template_subparser(subparser):
    parser = subparser.add_parser('template', help='Create a template of an interface, traces or part file, or the three files of an interface standard.')
    parser.add_argument('file_type', choices=['interface', 'traces', 'part', 'spi'], help='The file to create a template of, or spi for the three files of an SPI interface.')
    parser.add_argument('--output', help='Template file name.  The template is written to stdout without it.  For spi, the directory the three files are written to, the current directory without it.  An existing file is not overwritten.')
    parser.add_argument('--wires', type=int, choices=[3, 4], help='spi: the number of wires, 4.  3 is not supported yet.')
    parser.add_argument('--mode', type=int, choices=[0, 1, 2, 3], help='spi: the SPI mode.')
    parser.add_argument('--type', dest='spi_type', choices=['controller', 'peripheral'], help='spi: the role of the device.')
    parser.add_argument('--clock-period', type=float, help='spi: the period of the device clock that generates SCK, in ns.  10 without it.')
    parser.add_argument('--sck-period', type=float, help='spi: the period of SCK, in ns, an even number of device clock periods.  40 without it.')


def print_help_if_no_command_line_options_given(parser):
    '''
    Will print the help output if no command line arguments were given.
    '''
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(2)
