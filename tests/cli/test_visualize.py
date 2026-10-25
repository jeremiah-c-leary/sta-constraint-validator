import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__


def build_interface_text(lPorts, sMissingTimingReport):
    lText = []
    lText.append('description = "visualize test"')
    lText.append('interface = "DAC_SPI_1"')
    lText.append('part = "part.toml"')
    lText.append('traces = "traces.toml"')
    for sPort in lPorts:
        lText.append('')
        lText.append(sPort)
        lText.append(f'timing_reports = ["{sMissingTimingReport}"]')
    return '\n'.join(lText) + '\n'


def build_port_text(sName, fLaunchPeriod, fCapturePeriod, lSetupEdges, lHoldEdges):
    lText = []
    lText.append('[[port]]')
    lText.append(f'name = "{sName}"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append(f'launch_clock = {{name = "clk_launch", period = {fLaunchPeriod}, setup_edge = {lSetupEdges[0]}, hold_edge = {lHoldEdges[0]}}}')
    lText.append(f'capture_clock = {{port = "O_CLK", name = "clk_capture", period = {fCapturePeriod}, setup_edge = "{lSetupEdges[1]}", hold_edge = "{lHoldEdges[1]}"}}')
    return '\n'.join(lText)


class VisualizeTestCase(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        self.sInterfaceFile = os.path.join(self.sDirectory, 'interface.toml')
        self.sMissingTimingReport = os.path.join(self.sDirectory, 'not_written_yet.rpt')
        self.write_file('part.toml', '')
        self.write_file('traces.toml', '')

    def write_file(self, sFilename, sText):
        with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
            oFile.write(sText)

    def run_visualize_edges(self, lPorts):
        self.write_file('interface.toml', build_interface_text(lPorts, self.sMissingTimingReport))
        lArgv = ['stacv', 'visualize', 'edges', self.sInterfaceFile]
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', lArgv):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code


class TestVisualizeEdgesDispatch(VisualizeTestCase):

    def test_exits_with_zero_when_timing_reports_do_not_exist(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.assertEqual(0, self.run_visualize_edges([sPort]))

    def test_writes_nothing_to_stderr(self):
        sPort = build_port_text('O_DATA', 10, 40, [4, 'C'], [4, 'A'])
        self.run_visualize_edges([sPort])
        self.assertEqual('', self.oStderr.getvalue())

    def test_exits_with_two_on_interface_error(self):
        self.assertEqual(2, self.run_visualize_edges([]))

    def test_interface_error_is_written_to_stderr(self):
        self.run_visualize_edges([])
        self.assertRegex(self.oStderr.getvalue(), r'^ERROR: \[interface_config_002\] ')
