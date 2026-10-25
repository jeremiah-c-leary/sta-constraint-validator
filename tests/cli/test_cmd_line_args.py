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
        oArgs = parse_arguments(['check', 'interface.toml'])
        self.assertEqual('check', oArgs.which)

    def test_check_command_stores_interface_file(self):
        oArgs = parse_arguments(['check', 'interface.toml'])
        self.assertEqual('interface.toml', oArgs.interface_file)

    def test_check_command_requires_interface_file(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_arguments(['check'])

    def test_no_arguments_exits_with_two(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as oContext:
                parse_arguments([])
        self.assertEqual(2, oContext.exception.code)

    def test_check_report_option_stores_report_file(self):
        oArgs = parse_arguments(['check', 'interface.toml', '--report', 'stacv_report.txt'])
        self.assertEqual('stacv_report.txt', oArgs.report)

    def test_check_report_option_defaults_to_none(self):
        oArgs = parse_arguments(['check', 'interface.toml'])
        self.assertIsNone(oArgs.report)

    def test_check_junit_option_stores_junit_file(self):
        oArgs = parse_arguments(['check', 'interface.toml', '--junit', 'stacv_junit.xml'])
        self.assertEqual('stacv_junit.xml', oArgs.junit)

    def test_check_junit_option_defaults_to_none(self):
        oArgs = parse_arguments(['check', 'interface.toml'])
        self.assertIsNone(oArgs.junit)


class TestVisualizeSubparser(unittest.TestCase):

    def test_visualize_command_selects_visualize(self):
        oArgs = parse_arguments(['visualize', 'edges', 'interface.toml'])
        self.assertEqual('visualize', oArgs.which)

    def test_visualize_edges_stores_visualization(self):
        oArgs = parse_arguments(['visualize', 'edges', 'interface.toml'])
        self.assertEqual('edges', oArgs.visualization)

    def test_visualize_edges_stores_interface_file(self):
        oArgs = parse_arguments(['visualize', 'edges', 'interface.toml'])
        self.assertEqual('interface.toml', oArgs.interface_file)

    def test_visualize_command_requires_visualization(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_arguments(['visualize'])

    def test_visualize_edges_requires_interface_file(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_arguments(['visualize', 'edges'])
