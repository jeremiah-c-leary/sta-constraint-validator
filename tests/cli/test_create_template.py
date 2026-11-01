import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def read_example_template(sFileType):
    with open(os.path.join(sProjectDir, 'example', f'{sFileType}_template.toml')) as oFile:
        return oFile.read()


class TestCreateTemplate(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name

    def run_stacv(self, lArguments):
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv'] + lArguments):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def build_path(self, sFilename):
        return os.path.join(self.sDirectory, sFilename)

    def assert_template_written_to_stdout(self, sFileType):
        iExitCode = self.run_stacv(['create', 'template', sFileType])
        self.assertEqual(0, iExitCode)
        self.assertEqual(read_example_template(sFileType), self.oStdout.getvalue())

    def test_interface_template_is_the_example_interface_template(self):
        self.assert_template_written_to_stdout('interface')

    def test_traces_template_is_the_example_traces_template(self):
        self.assert_template_written_to_stdout('traces')

    def test_part_template_is_the_example_part_template(self):
        self.assert_template_written_to_stdout('part')

    def test_output_writes_the_template_to_a_file(self):
        sOutput = self.build_path('interface.toml')
        iExitCode = self.run_stacv(['create', 'template', 'interface', '--output', sOutput])
        self.assertEqual(0, iExitCode)
        self.assertEqual(f'Creating template {sOutput}\n', self.oStdout.getvalue())
        with open(sOutput) as oFile:
            self.assertEqual(read_example_template('interface'), oFile.read())

    def test_output_does_not_overwrite_an_existing_file(self):
        sOutput = self.build_path('part.toml')
        with open(sOutput, 'w') as oFile:
            oFile.write('filled in from the datasheet\n')
        iExitCode = self.run_stacv(['create', 'template', 'part', '--output', sOutput])
        self.assertEqual(2, iExitCode)
        self.assertEqual('', self.oStdout.getvalue())
        self.assertEqual(f'ERROR: [create_001] {sOutput} already exists; the template is not written\n', self.oStderr.getvalue())
        with open(sOutput) as oFile:
            self.assertEqual('filled in from the datasheet\n', oFile.read())

    def test_templates_written_together_run_through_visualize_and_generate(self):
        for sFileType in ['interface', 'traces', 'part']:
            self.assertEqual(0, self.run_stacv(['create', 'template', sFileType, '--output', self.build_path(f'{sFileType}.toml')]))
        sInterfaceFile = self.build_path('interface.toml')
        for lCommand in [['visualize', 'block_diagram'], ['visualize', 'edges'], ['generate', 'xdc'], ['generate', 'report_tcl']]:
            with self.subTest(command=' '.join(lCommand)):
                self.assertEqual(0, self.run_stacv(lCommand + [sInterfaceFile]))

    def test_unknown_file_type_is_a_usage_error(self):
        iExitCode = self.run_stacv(['create', 'template', 'device'])
        self.assertEqual(2, iExitCode)
        self.assertIn('usage:', self.oStderr.getvalue())

    def test_missing_file_type_is_a_usage_error(self):
        iExitCode = self.run_stacv(['create', 'template'])
        self.assertEqual(2, iExitCode)
        self.assertIn('usage:', self.oStderr.getvalue())

    def test_deferred_output_port_of_the_interface_template_has_no_edge_errors_when_analyzed(self):
        sTemplate = read_example_template('interface')
        sDeferredPort = 'status = "defer"\nname = "O_CS"'
        self.assertIn(sDeferredPort, sTemplate)
        sInterfaceFile = self.build_path('interface.toml')
        with open(sInterfaceFile, 'w') as oFile:
            oFile.write(sTemplate.replace(sDeferredPort, 'status = "analyze"\nname = "O_CS"'))
        iExitCode = self.run_stacv(['visualize', 'edges', sInterfaceFile])
        self.assertNotIn('ERROR', self.oStdout.getvalue() + self.oStderr.getvalue())
        self.assertEqual(0, iExitCode)
