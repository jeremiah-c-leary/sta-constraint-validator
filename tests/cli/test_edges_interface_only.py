import contextlib
import io
import os
from unittest import mock

from stacv import __main__
from tests.cli import test_interface_keys

build_interface = test_interface_keys.build_interface


class TestEdgesReadOnlyTheInterface(test_interface_keys.InterfaceTestCase):
    '''
    stacv visualize edges draws from the interface file alone, so the part and traces
    files can be written after the edges are found.
    '''

    def setUp(self):
        test_interface_keys.InterfaceTestCase.setUp(self)
        for sFilename in ['part.toml', 'traces.toml']:
            os.remove(os.path.join(self.sDirectory, sFilename))

    def test_edges_are_drawn_before_the_part_and_traces_files_exist(self):
        iExitCode = self.run_edges(build_interface())
        self.assertEqual('', self.oStderr.getvalue())
        self.assertIn('Port:  O_DATA', self.oStdout.getvalue())
        self.assertEqual(0, iExitCode)

    def test_edges_are_drawn_when_the_part_path_uses_a_variable_that_is_not_set(self):
        sPart = 'part = "$STACV_VARIABLE_THAT_IS_NOT_SET/part.toml"'
        iExitCode = self.run_edges(build_interface({'part': sPart}))
        self.assertEqual('', self.oStderr.getvalue())
        self.assertEqual(0, iExitCode)

    def test_part_key_is_still_required(self):
        self.assert_error({'part': None}, 'interface_config_002', 'missing required key "part"')

    def test_block_diagram_still_needs_the_part_file(self):
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(build_interface())
        oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv', 'visualize', 'block_diagram', self.sInterfaceFile]):
            with contextlib.redirect_stdout(io.StringIO()):
                with contextlib.redirect_stderr(oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        sPartFile = os.path.join(self.sDirectory, 'part.toml')
        self.assertEqual(f'ERROR: [interface_config_006] {self.sInterfaceFile} key "part" names a file that does not exist: {sPartFile}\n', oStderr.getvalue())
        self.assertEqual(2, oContext.exception.code)
