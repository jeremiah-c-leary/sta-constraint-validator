
class TimingReportFile():

    def __init__(self, sFilename, lLines):
        self.filename = sFilename
        self.lines = lLines


class TimingReportText():

    def __init__(self, oTimingReportFile, iFirstLineNumber, lLines):
        self.timing_report_file = oTimingReportFile
        self.first_line_number = iFirstLineNumber
        self.lines = lLines

    def line_number_of(self, iOffset=0):
        return self.first_line_number + iOffset

    def get_filename(self):
        return oTimingReportFile.filename
