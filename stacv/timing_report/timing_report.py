
class TimingReport():
    def __init__(self, oTimingReportText):
        self.text = oTimingReportText
        self.source = None
        self.destination = None
        self.process_corner = None
        self.capture_clock = None
        self.capture_clock_line = None
        self.launch_clock = None
        self.launch_clock_path = None
        self.data_path = None
        self.capture_clock_path = None
        self.launch_edge = None
        self.capture_edge = None
        self.clock_pessimism = None
        self.output_delay = None
        self.output_delay_line = None
        self.clock_uncertainty = None
        self.slack = None

    def get_lines(self):
        return self.text.lines

    def get_filename(self):
        return self.text.get_filename()

    def get_first_line_number(self):
        return self.text.first_line_number


class HoldTimingReport(TimingReport):
    def __init__(self, oTimingReportText):
        TimingReport.__init__(self, oTimingReportText)


class SetupTimingReport(TimingReport):
    def __init__(self, oTimingReportText):
        TimingReport.__init__(self, oTimingReportText)


class Clock():
    def __init__(self):
        self.name = None
        self.period = None
