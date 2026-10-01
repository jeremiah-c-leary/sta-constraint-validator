
class TimingReportFile():

    def __init__(self, sFilename, lLines):
        self.filename = sFilename
        self.lines = convert_strings_to_objects(sFilename, lLines)


class TimingReportText():

    def __init__(self, oTimingReportFile, lLines):
        self.timing_report_file = oTimingReportFile
        self.lines = lLines
        self.first_line_number = lLines[0].line_number

    def get_filename(self):
        return self.timing_report_file.filename


class ReportLine():

    def __init__(self, sFilename, sText, iLineNumber):
        self.text = sText
        self.line_number = iLineNumber
        self.filename = sFilename


def convert_strings_to_objects(sFilename, lLines):
    lReturn = []
    for iLine, sLine in enumerate(lLines, start=1):
        lReturn.append(ReportLine(sFilename, sLine, iLine))
    return lReturn
