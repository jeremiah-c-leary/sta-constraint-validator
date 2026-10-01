
import os
import unittest
import copy

from stacv.timing_report.xilinx import vivado
from stacv.timing_report import timing_report
from stacv.timing_report import timing_report_file
from stacv.timing_report import timing_report_parse_error

from tests import utils


sTestDir = os.path.dirname(__file__)
lSetupFile = utils.read_file(os.path.join(sTestDir, 'dac_spi.setup.rpt'))
lHoldFile = utils.read_file(os.path.join(sTestDir, 'dac_spi.hold.rpt'))
lTimingReportFile = utils.read_file(os.path.join(sTestDir, 'O_DAC_DATA_timing.rpt'))
oTimingReportFile = timing_report_file.TimingReportFile('O_DAC_DATA_timing.rpt', lTimingReportFile)


class Test(unittest.TestCase):

    @unittest.skip('rewriting parser to return objects.  Remove when completed.')
    def test_parse_output_setup_report(self):
        dExpected = build_output_setup_data_structure()

        self.assertEqual(dExpected, vivado.parse_timing_report(lSetupFile)[0])

    @unittest.skip('rewriting parser to return objects.  Remove when completed.')
    def test_parse_output_hold_report(self):
        dExpected = build_output_hold_data_structure()

        self.assertEqual(dExpected, vivado.parse_timing_report(lHoldFile)[0])

    @unittest.skip('rewriting parser to return objects.  Remove when completed.')
    def test_multiple_reports(self):
        self.maxDiff = None
        dSetupExpected = build_output_setup_data_structure()
        dHoldExpected = build_output_hold_data_structure()

        lInput = copy.deepcopy(lSetupFile)
        lInput.extend(copy.deepcopy(lHoldFile))

        lActual = vivado.parse_timing_report(lInput)

        self.assertEqual(dSetupExpected, lActual[0])
        self.assertEqual(dHoldExpected, lActual[1])

    def test_extract_timing_report_texts_finds_each_report(self):
        lReports = vivado.extract_timing_report_texts(oTimingReportFile)

        self.assertEqual(4, len(lReports))

        self.assertTrue(lReports[0].lines[0].text.startswith('Slack'))
        self.assertEqual(60, len(lReports[0].lines))
        self.assertTrue(lReports[0].lines[-1].text.strip().startswith('slack '))
        self.assertEqual(14, lReports[0].first_line_number)

        self.assertTrue(lReports[1].lines[0].text.startswith('Slack'))
        self.assertEqual(66, len(lReports[1].lines))
        self.assertTrue(lReports[1].lines[-1].text.strip().startswith('slack '))
        self.assertEqual(75, lReports[1].first_line_number)

        self.assertTrue(lReports[2].lines[0].text.startswith('Slack'))
        self.assertEqual(60, len(lReports[2].lines))
        self.assertTrue(lReports[2].lines[-1].text.strip().startswith('slack '))
        self.assertEqual(158, lReports[2].first_line_number)

        self.assertTrue(lReports[3].lines[0].text.startswith('Slack'))
        self.assertEqual(66, len(lReports[3].lines))
        self.assertTrue(lReports[3].lines[-1].text.strip().startswith('slack '))
        self.assertEqual(219, lReports[3].first_line_number)

    def test_parse_timing_report_returns_four_timing_reports(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        self.assertEqual(4, oTimingReports.number_of_timing_reports())

    def test_parse_timing_report_returns_a_hold_timing_report_object(self):

        self.assertTrue(isinstance(vivado.parse_timing_report(oTimingReportFile).reports[0], timing_report.HoldTimingReport))
        self.assertTrue(isinstance(vivado.parse_timing_report(oTimingReportFile).reports[2], timing_report.HoldTimingReport))

    def test_parse_timing_report_returns_a_setup_timing_report_object(self):

        self.assertTrue(isinstance(vivado.parse_timing_report(oTimingReportFile).reports[1], timing_report.SetupTimingReport))
        self.assertTrue(isinstance(vivado.parse_timing_report(oTimingReportFile).reports[3], timing_report.SetupTimingReport))

    def test_parse_timing_report_adds_report_text_to_timing_report_object(self):

        oTimingReportList = vivado.parse_timing_report(oTimingReportFile)

        self.assertEqual(60, len(oTimingReportList.reports[0].get_lines()))
        self.assertEqual(14, oTimingReportList.reports[0].text.first_line_number)

        self.assertEqual(66, len(oTimingReportList.reports[1].get_lines()))
        self.assertEqual(75, oTimingReportList.reports[1].text.first_line_number)

        self.assertEqual(60, len(oTimingReportList.reports[2].get_lines()))
        self.assertEqual(158, oTimingReportList.reports[2].text.first_line_number)

        self.assertEqual(66, len(oTimingReportList.reports[3].get_lines()))
        self.assertEqual(219, oTimingReportList.reports[3].text.first_line_number)

    def test_create_timing_report_raises_an_error_for_unknown_path_type(self):
        oTimingReportFile = timing_report_file.TimingReportFile('test', ['Slack (MET) :   1.000ns', '  Path Type:  Unexpected', '  slack   1.000'])
        oTimingReportText = timing_report_file.TimingReportText(oTimingReportFile, oTimingReportFile.lines)

        sError = r'ERROR: \[vivado_tr_parse_005\] test:2 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.create_timing_report(oTimingReportText)

    def test_extract_path_type_line_raises_error_if_no_path_type_line_exists(self):
        oTimingReportFile = timing_report_file.TimingReportFile('test', ['Slack (MET) :   1.000ns', '  Paths Type:  Unexpected', '  slack   1.000'])
        oTimingReportText = timing_report_file.TimingReportText(oTimingReportFile, oTimingReportFile.lines)

        sError = r'ERROR: \[vivado_tr_parse_004\] test:1 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.extract_path_type_line(oTimingReportText)

    def test_create_timing_report_raises_error_if_path_type_is_missing(self):
        oTimingReportFile = timing_report_file.TimingReportFile('test', ['Slack (MET) :   1.000ns', '  Path Type:  ', '  slack   1.000'])
        oTimingReportText = timing_report_file.TimingReportText(oTimingReportFile, oTimingReportFile.lines)

        sError = r'ERROR: \[vivado_tr_parse_005\] test:2 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.create_timing_report(oTimingReportText)

    def test_validate_timing_report_file_raises_error_if_an_ending_of_a_report_is_not_detected_at_the_end_of_a_file(self):
        lFile = []
        lFile.extend(['Slack (MET) :   1.000ns', '  Paths Type:  Min', '  slack   1.000'])
        lFile.extend([''])
        lFile.extend(['Slack (MET) :   2.000ns', '  Paths Type:  Max', '  slack   1.000'])
        lFile.extend([''])
        lFile.extend(['Slack (MET) :   2.000ns', '  Paths Type:  Max', '  slacks   1.000'])

        oTimingReportFile = timing_report_file.TimingReportFile('test', lFile)

        sError = r'ERROR: \[vivado_tr_parse_003\] test:9 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.validate_timing_report_file(oTimingReportFile)

    def test_validate_timing_report_file_raises_error_if_an_ending_of_a_report_is_not_detected_before_a_start_is_detected(self):
        lFile = []
        lFile.extend(['Slack (MET) :   1.000ns', '  Paths Type:  Min', '  slack   1.000'])
        lFile.extend([''])
        lFile.extend(['Slack (MET) :   2.000ns', '  Paths Type:  Max', '  slacks   1.000'])
        lFile.extend([''])
        lFile.extend(['Slack (MET) :   2.000ns', '  Paths Type:  Max', '  slack   1.000'])

        oTimingReportFile = timing_report_file.TimingReportFile('test', lFile)

        sError = r'ERROR: \[vivado_tr_parse_003\] test:5 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.validate_timing_report_file(oTimingReportFile)

    def test_validate_timing_report_file_raises_error_if_first_report_does_not_have_an_ending(self):
        lFile = []
        lFile.extend(['Slack (MET) :   1.000ns', '  Paths Type:  Min', '  slacks   1.000'])
        lFile.extend([''])
        lFile.extend(['Slack (MET) :   2.000ns', '  Paths Type:  Max', '  slack   1.000'])
        lFile.extend([''])
        lFile.extend(['Slack (MET) :   2.000ns', '  Paths Type:  Max', '  slack   1.000'])

        oTimingReportFile = timing_report_file.TimingReportFile('test', lFile)

        sError = r'ERROR: \[vivado_tr_parse_003\] test:1 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.validate_timing_report_file(oTimingReportFile)

    def test_validate_timing_report_file_raises_error_if_first_report_does_not_have_a_beginning(self):
        lFile = []
        lFile.extend(['Slacks (MET) :   1.000ns', '  Paths Type:  Min', '  slack   1.000'])
        lFile.extend([''])
        lFile.extend(['Slack (MET) :   2.000ns', '  Paths Type:  Max', '  slack   1.000'])
        lFile.extend([''])
        lFile.extend(['Slack (MET) :   2.000ns', '  Paths Type:  Max', '  slack   1.000'])

        oTimingReportFile = timing_report_file.TimingReportFile('test', lFile)

        sError = r'ERROR: \[vivado_tr_parse_002\] test:3 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.validate_timing_report_file(oTimingReportFile)

    def test_validate_timing_report_file_raises_error_if_no_timing_reports_found(self):
        lFile = []
        lFile.extend(['Slacks (MET) :   1.000ns', '  Paths Type:  Min', '  slacks   1.000'])
        lFile.extend([''])
        lFile.extend(['Slacks (MET) :   2.000ns', '  Paths Type:  Max', '  slacks   1.000'])
        lFile.extend([''])
        lFile.extend(['Slacks (MET) :   2.000ns', '  Paths Type:  Max', '  slacks   1.000'])

        oTimingReportFile = timing_report_file.TimingReportFile('test', lFile)

        sError = r'ERROR: \[vivado_tr_parse_001\] test:1 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.validate_timing_report_file(oTimingReportFile)

    def test_populate_timing_report_reports_source(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        oMyTimingReport = oTimingReports.reports[0]
        self.assertEqual(oMyTimingReport.source, 'q_spi_output_data_reg/C')

        oMyTimingReport = oTimingReports.reports[1]
        self.assertEqual(oMyTimingReport.source, 'q_spi_output_data_reg/C')

    def test_populate_timing_report_assert_error_if_no_source_is_found(self):

        lFile = []
        lFile.extend([''])
        lFile.extend([''])
        lFile.extend(['Slack (MET) :   1.000ns', '  Path Type:  Min', '  slack   1.000'])

        sError = r'ERROR: \[vivado_tr_parse_006\] test:3 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            populate_timing_report_from_lines(lFile)

    def test_populate_timing_report_reports_destination(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        oMyTimingReport = oTimingReports.reports[0]
        self.assertEqual(oMyTimingReport.destination, 'O_DAC_DATA')

        oMyTimingReport = oTimingReports.reports[1]
        self.assertEqual(oMyTimingReport.destination, 'O_DAC_DATA')

    def test_populate_timing_report_assert_error_if_no_destination_is_found(self):

        lFile = []
        lFile.extend([''])
        lFile.extend(['Slack (MET) :   1.000ns', '  Path Type:  Min', '  Source: something', '  slack   1.000'])

        sError = r'ERROR: \[vivado_tr_parse_007\] test:2 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            populate_timing_report_from_lines(lFile)

    def test_populate_timing_report_raises_error_if_source_has_no_value(self):
        lFile = ['', 'Slack (MET) :   1.000ns', '  Path Type:  Min', '  Source:', '  slack   1.000']

        sError = r'ERROR: \[vivado_tr_parse_006\] test:4 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            populate_timing_report_from_lines(lFile)

    def test_populate_timing_report_reports_process_corner(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        self.assertEqual('Fast', oTimingReports.reports[0].process_corner)
        self.assertEqual('Slow', oTimingReports.reports[2].process_corner)

    def test_populate_timing_report_raises_error_if_process_corner_is_missing(self):
        lFile = ['', 'Slack (MET) :   1.000ns', '  Source: a', '  Destination: b', '  Path Type:  Min', '  slack   1.000']

        sError = r'ERROR: \[vivado_tr_parse_008\] test:5 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            populate_timing_report_from_lines(lFile)

    def test_populate_timing_report_raises_error_if_process_corner_is_invalid(self):
        lFile = ['', 'Slack (MET) :   1.000ns', '  Source: a', '  Destination: b', '  Path Type:  Min at Typical Process Corner', '  slack   1.000']

        sError = r'ERROR: \[vivado_tr_parse_008\] test:5 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            populate_timing_report_from_lines(lFile)

    def test_populate_timing_report_reports_launch_clock(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        oLaunchClock = oTimingReports.reports[0].launch_clock
        self.assertEqual('clk_100mhz', oLaunchClock.name)
        self.assertEqual(10.0, oLaunchClock.period)

    def test_populate_timing_report_reports_capture_clock(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        oCaptureClock = oTimingReports.reports[0].capture_clock
        self.assertEqual('dac_sclk', oCaptureClock.name)
        self.assertEqual(50.0, oCaptureClock.period)

    def test_populate_timing_report_raises_error_if_launch_clock_is_missing(self):
        lFile = ['', 'Slack (MET) :   1.000ns', '  Source: a', '    (input port)', '  Destination: b', '    (output port clocked by dac_sclk  {rise@0.000ns fall@25.000ns period=50.000ns})', '  Path Type:  Min at Fast Process Corner', '  slack   1.000']

        sError = r'ERROR: \[vivado_tr_parse_009\] test:4 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            populate_timing_report_from_lines(lFile)

    def test_populate_timing_report_raises_error_if_clock_period_is_missing(self):
        lFile = ['', 'Slack (MET) :   1.000ns', '  Source: a', '    (rising edge-triggered cell FDCE clocked by clk_100mhz  {rise@0.000ns fall@5.000ns})', '  Destination: b', '    (output port clocked by dac_sclk  {rise@0.000ns fall@25.000ns period=50.000ns})', '  Path Type:  Min at Fast Process Corner', '  slack   1.000']

        sError = r'ERROR: \[vivado_tr_parse_010\] test:4 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            populate_timing_report_from_lines(lFile)

    def test_populate_timing_report_raises_error_if_clock_period_is_not_a_number(self):
        lFile = ['', 'Slack (MET) :   1.000ns', '  Source: a', '    (rising edge-triggered cell FDCE clocked by clk_100mhz  {rise@0.000ns fall@5.000ns period=ns})', '  Destination: b', '    (output port clocked by dac_sclk  {rise@0.000ns fall@25.000ns period=50.000ns})', '  Path Type:  Min at Fast Process Corner', '  slack   1.000']

        sError = r'ERROR: \[vivado_tr_parse_010\] test:4 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            populate_timing_report_from_lines(lFile)

    def test_validate_timing_report_file_raises_error_if_file_is_empty(self):

        oTimingReportFile = timing_report_file.TimingReportFile('test', [])

        sError = r'ERROR: \[vivado_tr_parse_001\] test:1 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.validate_timing_report_file(oTimingReportFile)

    def test_update_clock_period_raises_error_if_period_has_two_decimal_points(self):
        oLine = timing_report_file.ReportLine('test', '    (output port clocked by dac_sclk  {rise@0.000ns fall@25.000ns period=1.2.3ns})', 4)
        oClock = timing_report.Clock()

        sError = r'ERROR: \[vivado_tr_parse_010\] test:4 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.update_clock_period(oLine, oClock)

    def test_update_clock_period_raises_error_if_period_contains_letters(self):
        oLine = timing_report_file.ReportLine('test', '    (output port clocked by dac_sclk  {rise@0.000ns fall@25.000ns period=5x0ns})', 4)
        oClock = timing_report.Clock()

        sError = r'ERROR: \[vivado_tr_parse_010\] test:4 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.update_clock_period(oLine, oClock)

    def test_update_clock_period_raises_error_if_period_is_not_in_nanoseconds(self):
        oLine = timing_report_file.ReportLine('test', '    (output port clocked by dac_sclk  {rise@0.000ns fall@25.000ns period=10.000ps})', 4)
        oClock = timing_report.Clock()

        sError = r'ERROR: \[vivado_tr_parse_010\] test:4 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.update_clock_period(oLine, oClock)

    def test_update_clock_period_raises_error_if_period_is_negative(self):
        oLine = timing_report_file.ReportLine('test', '    (output port clocked by dac_sclk  {rise@0.000ns fall@25.000ns period=-5.000ns})', 4)
        oClock = timing_report.Clock()

        sError = r'ERROR: \[vivado_tr_parse_010\] test:4 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.update_clock_period(oLine, oClock)

    def test_update_clock_period_raises_error_if_period_is_zero(self):
        oLine = timing_report_file.ReportLine('test', '    (output port clocked by dac_sclk  {rise@0.000ns fall@25.000ns period=0.000ns})', 4)
        oClock = timing_report.Clock()

        sError = r'ERROR: \[vivado_tr_parse_010\] test:4 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.update_clock_period(oLine, oClock)

    def test_extract_launch_clock_path_lines_returns_lines_between_first_and_second_separator(self):
        oTimingReportText = vivado.extract_timing_report_texts(oTimingReportFile)[0]

        lLines = vivado.extract_launch_clock_path_lines(oTimingReportText)

        self.assertEqual(10, len(lLines))
        self.assertEqual(32, lLines[0].line_number)
        self.assertEqual(41, lLines[-1].line_number)

    def test_extract_data_path_lines_returns_lines_between_second_and_third_separator(self):
        oTimingReportText = vivado.extract_timing_report_texts(oTimingReportFile)[0]

        lLines = vivado.extract_data_path_lines(oTimingReportText)

        self.assertEqual(6, len(lLines))
        self.assertEqual(43, lLines[0].line_number)
        self.assertEqual(48, lLines[-1].line_number)

    def test_extract_capture_clock_path_lines_skips_blank_lines(self):
        oTimingReportText = vivado.extract_timing_report_texts(oTimingReportFile)[0]

        lLines = vivado.extract_capture_clock_path_lines(oTimingReportText)

        self.assertEqual(18, len(lLines))
        self.assertEqual(51, lLines[0].line_number)
        self.assertEqual(68, lLines[-1].line_number)

    def test_check_number_of_separators_raises_error_if_too_few_separators(self):
        oTimingReportFile = timing_report_file.TimingReportFile('test', ['Slack (MET) :   1.000ns', '  -------', '    K18   IBUF (Prop_ibuf_I_O)   0.160   0.160 r  I_CLK_IBUF_inst/O', '  -------', '  slack   1.000'])
        oTimingReportText = timing_report_file.TimingReportText(oTimingReportFile, oTimingReportFile.lines)

        sError = r'ERROR: \[vivado_tr_parse_011\] test:1 expected 5 separator lines but found 2'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.check_number_of_separators(oTimingReportText)

    def test_check_number_of_separators_raises_error_if_too_many_separators(self):
        lFile = []
        lFile.append('Slack (MET) :   1.000ns')
        for iSeparator in range(6):
            lFile.append('  -------')
        lFile.append('  slack   1.000')
        oTimingReportFile = timing_report_file.TimingReportFile('test', lFile)
        oTimingReportText = timing_report_file.TimingReportText(oTimingReportFile, oTimingReportFile.lines)

        sError = r'ERROR: \[vivado_tr_parse_011\] test:1 expected 5 separator lines but found 6'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.check_number_of_separators(oTimingReportText)


def populate_timing_report_from_lines(lFile):
    oTimingReportFile = timing_report_file.TimingReportFile('test', lFile)
    oTimingReportText = vivado.extract_timing_report_texts(oTimingReportFile)[0]
    oTimingReport = vivado.create_timing_report(oTimingReportText)
    vivado.populate_timing_report(oTimingReport)


def build_output_setup_data_structure():

    dReturn = {}
    dReturn['type'] = 'setup'
    dReturn['launch_edge'] = 40.000
    dReturn['capture_edge'] = 50.000
    dReturn['output_delay'] = 2.000
    dReturn['process_corner'] = 'Fast Process Corner'

    dReturn['data_path'] = []

    dReturn['data_path'].append(build_net_delay_structure(0, 0.000, 'I_CLK'))
    dReturn['data_path'].append(build_cell_delay_structure('K18', 'IBUF', 0.348, 'I_CLK_IBUF_inst/O'))
    dReturn['data_path'].append(build_net_delay_structure(1, 0.685, 'I_CLK_IBUF'))
    dReturn['data_path'].append(build_cell_delay_structure('BUFGCTRL_X0Y0', 'BUFG', 0.029, 'I_CLK_IBUF_BUFG_inst/O'))
    dReturn['data_path'].append(build_net_delay_structure(13, 0.862, 'I_CLK_IBUF_BUFG'))
    dReturn['data_path'].append(build_cell_delay_structure('SLICE_X0Y3', 'FDCE', 0.175, 'q_spi_output_data_reg/Q'))
    dReturn['data_path'].append(build_net_delay_structure(1, 0.600, 'O_DAC_DATA_OBUF'))
    dReturn['data_path'].append(build_cell_delay_structure('U16', 'OBUF', 1.285, 'O_DAC_DATA_OBUF_inst/O'))
    dReturn['data_path'].append(build_net_delay_structure(0, 0.000, 'O_DAC_DATA'))

    dReturn['required_path'] = []

    dReturn['required_path'].append(build_net_delay_structure(0, 0.000, 'I_CLK'))
    dReturn['required_path'].append(build_cell_delay_structure('K18', 'IBUF', 0.160, 'I_CLK_IBUF_inst/O'))
    dReturn['required_path'].append(build_net_delay_structure(1, 0.631, 'I_CLK_IBUF'))
    dReturn['required_path'].append(build_cell_delay_structure('BUFGCTRL_X0Y0', 'BUFG', 0.026, 'I_CLK_IBUF_BUFG_inst/O'))
    dReturn['required_path'].append(build_net_delay_structure(13, 0.591, 'I_CLK_IBUF_BUFG'))
    dReturn['required_path'].append(build_cell_delay_structure('SLICE_X0Y5', 'FDCE', 0.141, 'q_spi_output_clock_reg/Q'))
    dReturn['required_path'].append(build_net_delay_structure(1, 0.316, 'O_DAC_SCLK_OBUF'))
    dReturn['required_path'].append(build_cell_delay_structure('U15', 'OBUF', 1.101, 'O_DAC_SCLK_OBUF_inst/O'))
    dReturn['required_path'].append(build_net_delay_structure(0, 0.000, 'O_DAC_SCLK'))

    return dReturn


def build_output_hold_data_structure():

    dReturn = {}
    dReturn['type'] = 'hold'
    dReturn['launch_edge'] = 0.000
    dReturn['capture_edge'] = 0.000
    dReturn['output_delay'] = 1.000
    dReturn['process_corner'] = 'Fast Process Corner'

    dReturn['data_path'] = []

    dReturn['data_path'].append(build_net_delay_structure(0, 0.000, 'I_CLK'))
    dReturn['data_path'].append(build_cell_delay_structure('K18', 'IBUF', 0.160, 'I_CLK_IBUF_inst/O'))
    dReturn['data_path'].append(build_net_delay_structure(1, 0.631, 'I_CLK_IBUF'))
    dReturn['data_path'].append(build_cell_delay_structure('BUFGCTRL_X0Y0', 'BUFG', 0.026, 'I_CLK_IBUF_BUFG_inst/O'))
    dReturn['data_path'].append(build_net_delay_structure(13, 0.591, 'I_CLK_IBUF_BUFG'))
    dReturn['data_path'].append(build_cell_delay_structure('SLICE_X0Y3', 'FDCE', 0.141, 'q_spi_output_data_reg/Q'))
    dReturn['data_path'].append(build_net_delay_structure(1, 0.339, 'O_DAC_DATA_OBUF'))
    dReturn['data_path'].append(build_cell_delay_structure('U16', 'OBUF', 1.098, 'O_DAC_DATA_OBUF_inst/O'))
    dReturn['data_path'].append(build_net_delay_structure(0, 0.000, 'O_DAC_DATA'))

    dReturn['required_path'] = []

    dReturn['required_path'].append(build_net_delay_structure(0, 0.000, 'I_CLK'))
    dReturn['required_path'].append(build_cell_delay_structure('K18', 'IBUF', 0.348, 'I_CLK_IBUF_inst/O'))
    dReturn['required_path'].append(build_net_delay_structure(1, 0.685, 'I_CLK_IBUF'))
    dReturn['required_path'].append(build_cell_delay_structure('BUFGCTRL_X0Y0', 'BUFG', 0.029, 'I_CLK_IBUF_BUFG_inst/O'))
    dReturn['required_path'].append(build_net_delay_structure(13, 0.862, 'I_CLK_IBUF_BUFG'))
    dReturn['required_path'].append(build_cell_delay_structure('SLICE_X0Y5', 'FDCE', 0.175, 'q_spi_output_clock_reg/Q'))
    dReturn['required_path'].append(build_net_delay_structure(1, 0.572, 'O_DAC_SCLK_OBUF'))
    dReturn['required_path'].append(build_cell_delay_structure('U15', 'OBUF', 1.288, 'O_DAC_SCLK_OBUF_inst/O'))
    dReturn['required_path'].append(build_net_delay_structure(0, 0.000, 'O_DAC_SCLK'))

    return dReturn


def build_net_delay_structure(fan_out, delay, resource):
    dDelay = {}
    dDelay['type'] = 'net'
    dDelay['fan_out'] = fan_out
    dDelay['delay'] = delay
    dDelay['resource'] = resource
    return dDelay


def build_cell_delay_structure(location, delay_type, delay, resource):
    dDelay = {}
    dDelay['type'] = 'cell'
    dDelay['location'] = location
    dDelay['delay_type'] = delay_type
    dDelay['delay'] = delay
    dDelay['resource'] = resource
    return dDelay
