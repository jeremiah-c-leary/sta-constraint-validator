
class TimingReportFileParseError(ValueError):

    def __init__(self, sIdentifier, oLine, sMessage, oTypeReportText=None):
        self.identifier = sIdentifier
        self.filename = oLine.filename
        self.line_number = set_line_number(oLine, oTypeReportText)
        self.message = sMessage
        ValueError.__init__(self, f'ERROR: [{sIdentifier}] {self.filename}:{self.line_number} {sMessage}')


class TimingReportParseError(ValueError):

    def __init__(self, sIdentifier, oLine, sMessage, oTypeReportText=None):
        self.identifier = sIdentifier
        self.filename = oLine.filename
        self.line_number = set_line_number(oLine, oTypeReportText)
        self.message = sMessage
        ValueError.__init__(self, f'ERROR: [{sIdentifier}] {self.filename}:{self.line_number} {sMessage}')


def set_line_number(oLine, oTypeReportText):
    if oTypeReportText is None:
        return oLine.line_number
    return oTypeReportText.first_line_number
