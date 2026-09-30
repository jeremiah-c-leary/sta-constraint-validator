
import unittest

from stacv.timing_report import timing_report_file

class Test(unittest.TestCase):

    def test_timing_report_file_object_populates_filename_and_lines(self):

        oTimingReportFile = timing_report_file.TimingReportFile('my_file_name', ['first line', 'second line'])

        self.assertEqual(oTimingReportFile.filename, 'my_file_name')
        self.assertEqual(oTimingReportFile.lines[0], 'first line')
        self.assertEqual(oTimingReportFile.lines[1], 'second line')

    def test_timing_report_text_object_reports_location_in_timing_report_file_object(self):

        oTimingReportFile = timing_report_file.TimingReportFile('my_file_name', ['first line', 'second line'])

        oTimingReportText = timing_report_file.TimingReportText(oTimingReportFile, 32, ['my first line', 'my second line'])

        self.assertEqual(oTimingReportText.location_of(0), 32)
        self.assertEqual(oTimingReportText.location_of(10), 42)
