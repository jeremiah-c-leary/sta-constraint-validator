import os
import subprocess
import sys
import unittest

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


class TestModuleEntry(unittest.TestCase):
    '''
    stacv runs as a module, which is how an installed stacv command starts it too.
    '''

    def run_module(self, lArguments):
        return subprocess.run([sys.executable, '-m', 'stacv'] + lArguments, cwd=sProjectDir, capture_output=True, text=True)

    def test_module_without_a_command_prints_its_usage_and_exits_with_two(self):
        oResult = self.run_module([])
        self.assertTrue(oResult.stdout.startswith('usage: stacv '), oResult.stdout)
        self.assertEqual(2, oResult.returncode)

    def test_module_runs_a_command(self):
        oResult = self.run_module(['create', 'template', 'traces'])
        with open(os.path.join(sProjectDir, 'example', 'traces_template.toml')) as oFile:
            self.assertEqual(oFile.read(), oResult.stdout)
        self.assertEqual(0, oResult.returncode)
