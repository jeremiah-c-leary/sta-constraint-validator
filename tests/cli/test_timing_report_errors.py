import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sExampleDir = os.path.join(sProjectDir, 'example', 'texas_instruments', 'DAC81404')
sExampleReport = os.path.join(sExampleDir, 'timing_reports', 'O_DAC_DATA_timing.rpt')


def build_interface_text(sTimingReport):
    lText = []
    lText.append('description = "timing report errors test"')
    lText.append('name = "DAC_SPI_1"')
    lText.append(f'part = "{os.path.join(sExampleDir, "part.toml")}"')
    lText.append(f'traces = "{os.path.join(sExampleDir, "traces.toml")}"')
    lText.append('[[clock]]\nname = "clk_100mhz"\nperiod = 10.000')
    lText.append('[[clock]]\nname = "dac_sclk"\nperiod = 40.000\nport = "O_DAC_SCLK"')
    lText.append('generator = {source = "q_spi_output_clock_reg", master_pin = "C", target_pin = "Q", master_clock = "clk_100mhz"}')
    lText.append('[[port]]\nname = "O_DAC_DATA"\nmethodology = "SDR-SS-O"')
    lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 8}')
    lText.append('capture_clock = {name = "dac_sclk", setup_edge = "D", hold_edge = "B"}')
    lText.append(f'timing_reports = ["{sTimingReport}"]')
    return '\n'.join(lText) + '\n'


class TestTimingReportErrors(unittest.TestCase):
    '''
    The example's passing timing report is copied with one line changed, and read by stacv check.
    '''

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sTimingReport = os.path.join(oTemporaryDirectory.name, 'O_DAC_DATA_timing.rpt')
        self.sInterfaceFile = os.path.join(oTemporaryDirectory.name, 'interface.toml')
        with open(self.sInterfaceFile, 'w') as oFile:
            oFile.write(build_interface_text(self.sTimingReport))
        with open(sExampleReport) as oFile:
            self.lLines = oFile.read().split('\n')

    def change_line(self, iLineNumber, sOld, sNew):
        sLine = self.lLines[iLineNumber - 1]
        self.assertIn(sOld, sLine)
        self.lLines[iLineNumber - 1] = sLine.replace(sOld, sNew, 1)

    def run_check(self):
        with open(self.sTimingReport, 'w') as oFile:
            oFile.write('\n'.join(self.lLines))
        oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv', 'check', self.sInterfaceFile]):
            with contextlib.redirect_stdout(io.StringIO()):
                with contextlib.redirect_stderr(oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        self.assertEqual(2, oContext.exception.code)
        return oStderr.getvalue()

    def assert_error(self, sIdentifier, iLineNumber, sMessage):
        self.assertEqual(f'ERROR: [{sIdentifier}] {self.sTimingReport}:{iLineNumber} {sMessage}\n', self.run_check())

    def test_example_report_passes(self):
        with open(self.sTimingReport, 'w') as oFile:
            oFile.write('\n'.join(self.lLines))
        with mock.patch('sys.argv', ['stacv', 'check', self.sInterfaceFile]):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as oContext:
                    __main__.main()
        self.assertEqual(0, oContext.exception.code)

    def test_file_without_timing_reports(self):
        self.lLines = ['']
        self.assert_error('vivado_tr_parse_001', 1, 'has no timing reports')

    def test_unknown_path_type(self):
        self.change_line(20, 'Max at', 'Mid at')
        self.assert_error('vivado_tr_parse_005', 20, '"Path Type:" must be Max or Min')

    def test_unknown_process_corner(self):
        self.change_line(20, 'Slow Process', 'Typical Process')
        self.assert_error('vivado_tr_parse_008', 20, '"Path Type:" must name the Slow or Fast process corner')

    def test_clock_period_in_other_units(self):
        self.change_line(16, 'period=10.000ns', 'period=10.000ps')
        self.assert_error('vivado_tr_parse_010', 16, 'clock period must be in ns')

    def test_zero_clock_period(self):
        self.change_line(16, 'period=10.000ns', 'period=0.000ns')
        self.assert_error('vivado_tr_parse_010', 16, 'clock period must be greater than 0')

    def test_output_delay_in_other_units(self):
        self.change_line(24, '12.000ns', '12.000ps')
        self.assert_error('vivado_tr_parse_015', 24, '"Output Delay:" must be in ns')

    def test_requirement_in_other_units(self):
        self.change_line(21, 'Requirement:            20.000ns', 'Requirement:            20.000ps')
        self.assert_error('vivado_tr_parse_015', 21, '"Requirement:" must be in ns')

    def test_slack_that_is_not_a_number_of_ns(self):
        self.change_line(14, '7.524ns', 'none')
        self.assert_error('vivado_tr_parse_016', 14, 'slack must be a number of ns')
