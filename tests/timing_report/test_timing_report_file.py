
import unittest

from stacv.timing_report import timing_report_file

class Test(unittest.TestCase):

    def test_timing_report_file_object_populates_filename_and_lines(self):

        oTimingReportFile = timing_report_file.TimingReportFile('my_file_name', ['first line', 'second line'])

        self.assertEqual(oTimingReportFile.filename, 'my_file_name')
        self.assertEqual(oTimingReportFile.lines[0].text, 'first line')
        self.assertEqual(oTimingReportFile.lines[1].text, 'second line')

    def test_timing_report_text_object_reports_location_in_timing_report_file_object(self):

        oTimingReportFile = timing_report_file.TimingReportFile('my_file_name', ['first line', 'second line', 'third line', 'fourth line'])

        oTimingReportText = timing_report_file.TimingReportText(oTimingReportFile, oTimingReportFile.lines)
        self.assertEqual(oTimingReportText.first_line_number, 1)

        oTimingReportText = timing_report_file.TimingReportText(oTimingReportFile, oTimingReportFile.lines[1::])
        self.assertEqual(oTimingReportText.first_line_number, 2)

        oTimingReportText = timing_report_file.TimingReportText(oTimingReportFile, oTimingReportFile.lines[2::])
        self.assertEqual(oTimingReportText.first_line_number, 3)

    def test_report_line_object_reports_text_line_number_and_filename(self):

        oReportLine = timing_report_file.ReportLine('my_file_name', 'my text', 7)

        self.assertEqual(oReportLine.text, 'my text')
        self.assertEqual(oReportLine.line_number, 7)
        self.assertEqual(oReportLine.filename, 'my_file_name')

    def test_timing_report_file_object_creates_report_lines_numbered_from_one(self):

        oTimingReportFile = timing_report_file.TimingReportFile('my_file_name', ['first line', 'second line'])

        self.assertEqual(oTimingReportFile.filename, 'my_file_name')
        self.assertEqual(oTimingReportFile.lines[0].text, 'first line')
        self.assertEqual(oTimingReportFile.lines[0].line_number, 1)
        self.assertEqual(oTimingReportFile.lines[1].text, 'second line')
        self.assertEqual(oTimingReportFile.lines[1].line_number, 2)

    def test_report_lines_point_back_to_their_timing_report_file(self):

        oTimingReportFile = timing_report_file.TimingReportFile('my_file_name', ['first line'])

        self.assertEqual(oTimingReportFile.lines[0].filename, 'my_file_name')
