import sys

from stacv.cli import cmd_line_args
from stacv.cli import debug
from stacv.cli import report
from stacv.cli import check


def main():
    '''
    Main routine of the STA Constraint Validator program.
    '''

    command_line_arguments = cmd_line_args.parse_command_line_arguments()
    iExitCode = 0

    if command_line_arguments.which == 'debug':
        debug.execute(command_line_arguments)
    elif command_line_arguments.which == 'report':
        sys.exit(report.execute(command_line_arguments))
    elif command_line_arguments.which == 'check':
        iExitCode = check.execute(command_line_arguments)

    sys.exit(iExitCode)


def list_checks(args):
    import textwrap
    from stacv.analysis import registry
    if args.rst:
        with open(args.rst, 'w', encoding='utf-8') as handle:
            handle.write(registry.to_rst())
        print(f'Check documentation written to {args.rst}')
        return
    for check in registry.CHECKS:
        did = f'  [DID {check.did}]' if check.did else ''
        print(f'{check.check_id}  {check.title}{did}')
        for line in textwrap.wrap(check.description, 72):
            print(f'         {line}')
        print()
