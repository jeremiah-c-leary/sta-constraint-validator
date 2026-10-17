
from stacv.timing_report import timing_report


class TimingReportList():
    def __init__(self):
        self.reports = []

    def add(self, oTimingReport):
        self.reports.append(oTimingReport)

    def extend(self, oTimingReportList):
        self.reports.extend(oTimingReportList.reports)

    def number_of_timing_reports(self):
        return len(self.reports)

    def get_setup_reports(self):
        lReports = []
        for oReport in self.reports:
            if isinstance(oReport, timing_report.SetupTimingReport):
                lReports.append(oReport)
        return lReports

    def get_hold_reports(self):
        lReports = []
        for oReport in self.reports:
            if isinstance(oReport, timing_report.HoldTimingReport):
                lReports.append(oReport)
        return lReports
