
class TimingReportList():
    def __init__(self):
        self.reports = []

    def add(self, oTimingReport):
        self.reports.append(oTimingReport)

    def number_of_timing_reports(self):
        return len(self.reports)
