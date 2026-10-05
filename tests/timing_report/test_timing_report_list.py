
import unittest

from stacv.timing_report import timing_report
from stacv.timing_report import timing_report_list


class Test(unittest.TestCase):

    def setUp(self):
        self.oFirstHoldReport = timing_report.HoldTimingReport(None)
        self.oFirstSetupReport = timing_report.SetupTimingReport(None)
        self.oSecondHoldReport = timing_report.HoldTimingReport(None)
        self.oSecondSetupReport = timing_report.SetupTimingReport(None)

        self.oMixedReports = timing_report_list.TimingReportList()
        self.oMixedReports.add(self.oFirstHoldReport)
        self.oMixedReports.add(self.oFirstSetupReport)
        self.oMixedReports.add(self.oSecondHoldReport)
        self.oMixedReports.add(self.oSecondSetupReport)

    def test_get_setup_reports_returns_only_setup_reports_in_order(self):
        lExpected = [self.oFirstSetupReport, self.oSecondSetupReport]

        self.assertEqual(lExpected, self.oMixedReports.get_setup_reports())

    def test_get_hold_reports_returns_only_hold_reports_in_order(self):
        lExpected = [self.oFirstHoldReport, self.oSecondHoldReport]

        self.assertEqual(lExpected, self.oMixedReports.get_hold_reports())

    def test_get_setup_reports_returns_empty_list_when_only_hold_reports(self):
        oHoldReports = timing_report_list.TimingReportList()
        oHoldReports.add(timing_report.HoldTimingReport(None))

        self.assertEqual([], oHoldReports.get_setup_reports())

    def test_get_hold_reports_returns_empty_list_when_only_setup_reports(self):
        oSetupReports = timing_report_list.TimingReportList()
        oSetupReports.add(timing_report.SetupTimingReport(None))

        self.assertEqual([], oSetupReports.get_hold_reports())

    def test_getters_return_empty_list_for_empty_timing_report_list(self):
        oEmptyReports = timing_report_list.TimingReportList()

        self.assertEqual([], oEmptyReports.get_setup_reports())
        self.assertEqual([], oEmptyReports.get_hold_reports())
