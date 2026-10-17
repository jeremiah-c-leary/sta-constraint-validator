import contextlib
import io
import unittest
from unittest import mock

from stacv.cli import cmd_line_args


def parse_arguments(lArguments):
    lArgv = ['stacv']
    lArgv.extend(lArguments)
    with mock.patch('sys.argv', lArgv):
        return cmd_line_args.parse_command_line_arguments()


class TestCheckSubparser(unittest.TestCase):

    def test_check_command_selects_check(self):
        oArgs = parse_arguments(['check', 'stacv.toml'])
        self.assertEqual('check', oArgs.which)

    def test_check_command_stores_config_file(self):
        oArgs = parse_arguments(['check', 'stacv.toml'])
        self.assertEqual('stacv.toml', oArgs.config_file)

    def test_check_command_requires_config_file(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_arguments(['check'])
