import contextlib
import io
import unittest
from unittest import mock

from stacv import __main__


class TestUsageHelp(unittest.TestCase):
    '''
    A missing or wrong argument prints the help of the command it was given to,
    then the error, so a user can find the next word without reading the docs.
    '''

    def run_stacv(self, lArguments):
        oStdout = io.StringIO()
        oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv'] + lArguments):
            with contextlib.redirect_stdout(oStdout):
                with contextlib.redirect_stderr(oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code, oStdout.getvalue(), oStderr.getvalue()

    def read_help(self, lCommand):
        iExitCode, sStdout, sStderr = self.run_stacv(lCommand + ['--help'])
        return sStdout

    def assert_help_then_error(self, lArguments, lCommand, sError):
        iExitCode, sStdout, sStderr = self.run_stacv(lArguments)
        sExpected = self.read_help(lCommand) + '\n' + ' '.join(['stacv'] + lCommand) + ': error: ' + sError + '\n'
        self.assertEqual(2, iExitCode)
        self.assertEqual('', sStdout)
        self.assertEqual(sExpected, sStderr)

    def test_unknown_command_prints_stacv_help(self):
        self.assert_help_then_error(['validate'], [], "argument {check,visualize,generate,create}: invalid choice: 'validate' (choose from 'check', 'visualize', 'generate', 'create')")

    def test_check_without_interface_file_prints_check_help(self):
        self.assert_help_then_error(['check'], ['check'], 'the following arguments are required: interface_file')

    def test_visualize_without_visualization_prints_visualize_help(self):
        self.assert_help_then_error(['visualize'], ['visualize'], 'the following arguments are required: visualization')

    def test_visualize_edges_without_interface_file_prints_edges_help(self):
        self.assert_help_then_error(['visualize', 'edges'], ['visualize', 'edges'], 'the following arguments are required: interface_file')

    def test_generate_without_target_prints_generate_help(self):
        self.assert_help_then_error(['generate'], ['generate'], 'the following arguments are required: target')

    def test_generate_xdc_without_interface_file_prints_xdc_help(self):
        self.assert_help_then_error(['generate', 'xdc'], ['generate', 'xdc'], 'the following arguments are required: interface_file')

    def test_generate_report_tcl_without_interface_file_prints_report_tcl_help(self):
        self.assert_help_then_error(['generate', 'report_tcl'], ['generate', 'report_tcl'], 'the following arguments are required: interface_file')

    def test_create_without_target_prints_create_help(self):
        self.assert_help_then_error(['create'], ['create'], 'the following arguments are required: target')

    def test_create_template_without_file_type_prints_template_help(self):
        self.assert_help_then_error(['create', 'template'], ['create', 'template'], 'the following arguments are required: file_type')

    def test_create_template_with_unknown_file_type_prints_template_help(self):
        self.assert_help_then_error(['create', 'template', 'device'], ['create', 'template'], "argument file_type: invalid choice: 'device' (choose from 'interface', 'traces', 'part')")
