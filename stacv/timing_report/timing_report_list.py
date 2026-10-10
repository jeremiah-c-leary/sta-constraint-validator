
from stacv.timing_report import timing_report


class TimingReportList():
    def __init__(self):
        self.reports = []

    def add(self, oTimingReport):
        self.reports.append(oTimingReport)

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

    def get_output_delay_lines(self):
        lOutputDelayLines = []
        for oReport in self.reports:
            lOutputDelayLines.append(oReport.get_output_delay_line())
        return lOutputDelayLines

    def get_output_delays(self):
        lOutputDelayLines = []
        for oReport in self.reports:
            lOutputDelayLines.append(oReport.get_output_delay())
        return lOutputDelayLines
