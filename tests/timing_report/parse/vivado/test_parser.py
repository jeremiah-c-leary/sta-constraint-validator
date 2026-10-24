
import os
import unittest
import copy

from stacv.timing_report.xilinx import vivado
from stacv.timing_report import timing_report
from stacv.timing_report import timing_report_file
from stacv.timing_report import timing_report_parse_error
from stacv.timing_report import delay_element
from stacv.timing_report import delay_path

from tests import utils


sTestDir = os.path.dirname(__file__)
lTimingReportFile = utils.read_file(os.path.join(sTestDir, 'O_DAC_DATA_timing.rpt'))
oTimingReportFile = timing_report_file.TimingReportFile('O_DAC_DATA_timing.rpt', lTimingReportFile)


class Test(unittest.TestCase):

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
        self.assertEqual(14, oTimingReportList.reports[0].get_first_line_number())

        self.assertEqual(66, len(oTimingReportList.reports[1].get_lines()))
        self.assertEqual(75, oTimingReportList.reports[1].get_first_line_number())

        self.assertEqual(60, len(oTimingReportList.reports[2].get_lines()))
        self.assertEqual(158, oTimingReportList.reports[2].get_first_line_number())

        self.assertEqual(66, len(oTimingReportList.reports[3].get_lines()))
        self.assertEqual(219, oTimingReportList.reports[3].get_first_line_number())

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

    def test_create_delay_returns_cell_delay_for_cell_row(self):
        oLine = timing_report_file.ReportLine('test', '    K18                  IBUF (Prop_ibuf_I_O)         0.160     0.160 r  I_CLK_IBUF_inst/O', 36)

        oDelay = vivado.create_delay(oLine)

        self.assertTrue(isinstance(oDelay, delay_element.CellDelay))
        self.assertEqual('K18', oDelay.location)
        self.assertEqual('IBUF', oDelay.delay_type)
        self.assertEqual(0.160, oDelay.delay)
        self.assertEqual('I_CLK_IBUF_inst/O', oDelay.resource)

    def test_create_delay_returns_cell_delay_for_flip_flop_clock_to_out_row(self):
        oLine = timing_report_file.ReportLine('test', '    SLICE_X0Y3           FDCE (Prop_fdce_C_Q)         0.141     1.549 r  q_spi_output_data_reg/Q', 43)

        oDelay = vivado.create_delay(oLine)

        self.assertTrue(isinstance(oDelay, delay_element.CellDelay))
        self.assertEqual('SLICE_X0Y3', oDelay.location)
        self.assertEqual('FDCE', oDelay.delay_type)
        self.assertEqual(0.141, oDelay.delay)
        self.assertEqual('q_spi_output_data_reg/Q', oDelay.resource)

    def test_create_delay_returns_net_delay_for_routed_net_row(self):
        oLine = timing_report_file.ReportLine('test', '                         net (fo=13, routed)          0.591     1.408    I_CLK_IBUF_BUFG', 40)

        oDelay = vivado.create_delay(oLine)

        self.assertTrue(isinstance(oDelay, delay_element.NetDelay))
        self.assertEqual(13, oDelay.fan_out)
        self.assertEqual(0.591, oDelay.delay)
        self.assertEqual('I_CLK_IBUF_BUFG', oDelay.resource)

    def test_create_delay_returns_net_delay_for_unrouted_net_row(self):
        oLine = timing_report_file.ReportLine('test', '                         net (fo=0)                   0.000     0.000    I_CLK', 34)

        oDelay = vivado.create_delay(oLine)

        self.assertTrue(isinstance(oDelay, delay_element.NetDelay))
        self.assertEqual(0, oDelay.fan_out)
        self.assertEqual(0.000, oDelay.delay)
        self.assertEqual('I_CLK', oDelay.resource)

    def test_create_delay_reads_row_from_report_file(self):
        oLine = oTimingReportFile.lines[39]

        oDelay = vivado.create_delay(oLine)

        self.assertTrue(isinstance(oDelay, delay_element.NetDelay))
        self.assertEqual(13, oDelay.fan_out)
        self.assertEqual(0.591, oDelay.delay)
        self.assertEqual('I_CLK_IBUF_BUFG', oDelay.resource)

    def test_is_delay_row_returns_true_for_cell_row(self):
        oLine = timing_report_file.ReportLine('test', '    K18                  IBUF (Prop_ibuf_I_O)         0.160     0.160 r  I_CLK_IBUF_inst/O', 36)

        self.assertTrue(vivado.is_delay_row(oLine))

    def test_is_delay_row_returns_true_for_net_row(self):
        oLine = timing_report_file.ReportLine('test', '                         net (fo=13, routed)          0.591     1.408    I_CLK_IBUF_BUFG', 40)

        self.assertTrue(vivado.is_delay_row(oLine))

    def test_is_delay_row_returns_false_for_clock_edge_row(self):
        oLine = timing_report_file.ReportLine('test', '                         (clock clk_100mhz rise edge)     0.000     0.000 r  ', 32)

        self.assertFalse(vivado.is_delay_row(oLine))

    def test_is_delay_row_returns_false_for_port_row(self):
        oLine = timing_report_file.ReportLine('test', '    K18                                               0.000     0.000 r  I_CLK (IN)', 33)

        self.assertFalse(vivado.is_delay_row(oLine))

    def test_is_delay_row_returns_false_for_pin_row(self):
        oLine = timing_report_file.ReportLine('test', '    K18                                                               r  I_CLK_IBUF_inst/I', 35)

        self.assertFalse(vivado.is_delay_row(oLine))

    def test_is_delay_row_returns_false_for_clock_pessimism_row(self):
        oLine = timing_report_file.ReportLine('test', '                         clock pessimism             -0.245     3.714    ', 67)

        self.assertFalse(vivado.is_delay_row(oLine))

    def test_is_delay_row_returns_false_for_clock_uncertainty_row(self):
        oLine = timing_report_file.ReportLine('test', '                         clock uncertainty   -0.035 53.176    ', 134)

        self.assertFalse(vivado.is_delay_row(oLine))

    def test_is_delay_row_returns_false_for_output_delay_row(self):
        oLine = timing_report_file.ReportLine('test', '                         output delay                -1.000     2.714    ', 68)

        self.assertFalse(vivado.is_delay_row(oLine))

    def test_is_delay_row_returns_true_for_unrouted_net_row(self):
        oLine = timing_report_file.ReportLine('test', '                         net (fo=0)                   0.000     0.000    I_CLK', 37)

        self.assertTrue(vivado.is_delay_row(oLine))

    def test_create_delay_path_keeps_only_delay_rows(self):
        oTimingReportText = vivado.extract_timing_report_texts(oTimingReportFile)[0]
        lLines = vivado.extract_launch_clock_path_lines(oTimingReportText)

        oDelayPath = vivado.create_delay_path(lLines)

        self.assertTrue(isinstance(oDelayPath, delay_path.DelayPath))
        self.assertEqual(5, len(oDelayPath.delays))
        self.assertEqual('I_CLK', oDelayPath.delays[0].resource)
        self.assertEqual('I_CLK_IBUF_BUFG', oDelayPath.delays[-1].resource)

    def test_create_delay_path_keeps_first_line_of_path(self):
        oTimingReportText = vivado.extract_timing_report_texts(oTimingReportFile)[0]
        lLines = vivado.extract_launch_clock_path_lines(oTimingReportText)

        oDelayPath = vivado.create_delay_path(lLines)

        self.assertEqual('O_DAC_DATA_timing.rpt', oDelayPath.first_line.filename)
        self.assertEqual(32, oDelayPath.first_line.line_number)

    def test_populate_timing_report_reports_launch_clock_path(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        self.assertEqual(1.408, oTimingReports.reports[0].launch_clock_path.total_delay())
        self.assertEqual(1.924, oTimingReports.reports[1].launch_clock_path.total_delay())

    def test_populate_timing_report_reports_data_path(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        self.assertEqual(1.578, oTimingReports.reports[0].data_path.total_delay())
        self.assertEqual(2.060, oTimingReports.reports[1].data_path.total_delay())

    def test_populate_timing_report_reports_capture_clock_path(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        self.assertEqual(3.959, oTimingReports.reports[0].capture_clock_path.total_delay())
        self.assertEqual(2.966, oTimingReports.reports[1].capture_clock_path.total_delay())

    def test_populate_timing_report_reports_launch_edge(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        self.assertEqual(0.000, oTimingReports.reports[0].launch_edge)
        self.assertEqual(40.000, oTimingReports.reports[1].launch_edge)

    def test_populate_timing_report_reports_capture_edge(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        self.assertEqual(0.000, oTimingReports.reports[0].capture_edge)
        self.assertEqual(50.000, oTimingReports.reports[1].capture_edge)

    def test_populate_timing_report_reports_clock_pessimism(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        self.assertEqual(0.245, oTimingReports.reports[0].clock_pessimism)
        self.assertEqual(0.245, oTimingReports.reports[1].clock_pessimism)

    def test_update_clock_pessimism_raises_error_if_line_is_missing(self):
        oTimingReportFile = timing_report_file.TimingReportFile('test', ['Slack (MET) :   1.000ns', '  Path Type:  Max at Slow Process Corner', '  slack   1.000'])
        oTimingReportText = timing_report_file.TimingReportText(oTimingReportFile, oTimingReportFile.lines)
        oTimingReport = timing_report.SetupTimingReport(oTimingReportText)

        sError = r'ERROR: \[vivado_tr_parse_012\] test:1 .*'
        with self.assertRaisesRegex(timing_report_parse_error.TimingReportParseError, sError):
            vivado.update_clock_pessimism(oTimingReport)

    def test_populate_timing_report_reports_output_delay(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        self.assertEqual(1.000, oTimingReports.reports[0].output_delay)
        self.assertEqual(2.000, oTimingReports.reports[1].output_delay)

    def test_populate_timing_report_reports_clock_uncertainty(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        self.assertEqual(0.035, oTimingReports.reports[1].clock_uncertainty)

    def test_populate_timing_report_leaves_clock_uncertainty_empty_when_not_reported(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        self.assertIsNone(oTimingReports.reports[0].clock_uncertainty)

    def test_populate_timing_report_reports_slack(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        self.assertEqual(0.272, oTimingReports.reports[0].slack)
        self.assertEqual(7.192, oTimingReports.reports[1].slack)

    def test_update_slack_reads_violated_slack(self):
        oTimingReportFile = timing_report_file.TimingReportFile('test', ['Slack (VIOLATED) :        -0.123ns  (required time - arrival time)', '  slack   -0.123'])
        oTimingReportText = timing_report_file.TimingReportText(oTimingReportFile, oTimingReportFile.lines)
        oTimingReport = timing_report.SetupTimingReport(oTimingReportText)

        vivado.update_slack(oTimingReport)

        self.assertEqual(-0.123, oTimingReport.slack)

    def test_populate_timing_report_reports_output_delay_line(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        oOutputDelayLine = oTimingReports.reports[1].output_delay_line

        self.assertEqual('O_DAC_DATA_timing.rpt', oOutputDelayLine.filename)
        self.assertEqual(85, oOutputDelayLine.line_number)

    def test_populate_timing_report_reports_capture_clock_line(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        oCaptureClockLine = oTimingReports.reports[1].capture_clock_line

        self.assertEqual('O_DAC_DATA_timing.rpt', oCaptureClockLine.filename)
        self.assertEqual(79, oCaptureClockLine.line_number)

    def test_populate_timing_report_reports_launch_clock_line(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        oLaunchClockLine = oTimingReports.reports[1].launch_clock_line

        self.assertEqual('O_DAC_DATA_timing.rpt', oLaunchClockLine.filename)
        self.assertEqual(77, oLaunchClockLine.line_number)

    def test_populate_timing_report_reports_requirement_line(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        oRequirementLine = oTimingReports.reports[1].requirement_line

        self.assertEqual('O_DAC_DATA_timing.rpt', oRequirementLine.filename)
        self.assertEqual(82, oRequirementLine.line_number)

    def test_populate_timing_report_reports_rising_capture_clock_edge_type(self):
        oTimingReports = vivado.parse_timing_report(oTimingReportFile)

        self.assertEqual('rise', oTimingReports.reports[0].capture_clock_edge_type)
        self.assertEqual('rise', oTimingReports.reports[1].capture_clock_edge_type)

    def test_populate_timing_report_reports_falling_capture_clock_edge_type(self):
        lFallingTimingReportFile = []
        for sLine in lTimingReportFile:
            lFallingTimingReportFile.append(sLine.replace('dac_sclk rise@', 'dac_sclk fall@'))
        oFallingTimingReportFile = timing_report_file.TimingReportFile('O_DAC_DATA_timing.rpt', lFallingTimingReportFile)

        oTimingReports = vivado.parse_timing_report(oFallingTimingReportFile)

        self.assertEqual('fall', oTimingReports.reports[0].capture_clock_edge_type)
        self.assertEqual('fall', oTimingReports.reports[1].capture_clock_edge_type)


def populate_timing_report_from_lines(lFile):
    oTimingReportFile = timing_report_file.TimingReportFile('test', lFile)
    oTimingReportText = vivado.extract_timing_report_texts(oTimingReportFile)[0]
    oTimingReport = vivado.create_timing_report(oTimingReportText)
    vivado.populate_timing_report(oTimingReport)
