'''
stacv report: validate timing reports against the intent.

Prints a summary, optionally writes a JUnit XML file, and returns a non-zero exit code when any check fails so CI/CD
pipelines stop the build.
'''

from stacv import utils
from stacv.analysis import checks

MARK = {checks.PASS: 'pass', checks.FAIL: 'FAIL', checks.SKIP: 'skip'}


def execute(args):
    config = utils.read_config_file(args.config_file)
    report_paths = checks.load_reports(args.reports)
    validations = checks.validate(config, report_paths, tuple(args.corners))

    print_summary(validations)

    if args.junit:
        from stacv.output import junit
        junit.write(validations, args.junit)
        print(f'JUnit results written to {args.junit}')

    return 1 if any(v.status == checks.FAIL for v in validations) else 0


def print_summary(validations):
    for validation in validations:
        print(f'{validation.name}')
        for result in validation.results:
            print(f'  [{MARK[result.status]}] {result.check_id} {result.title}')
            if result.status == checks.FAIL:
                print(f'         {result.message}')
    failed = sum(v.count(checks.FAIL) for v in validations)
    skipped = sum(v.count(checks.SKIP) for v in validations)
    passed = sum(v.count(checks.PASS) for v in validations)
    print(f'\n{passed} passed, {failed} failed, {skipped} skipped')
