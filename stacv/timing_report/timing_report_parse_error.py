
class TimingReportParseError(ValueError):

    def __init__(self, sIdentifier, oLine, sMessage):
        self.identifier = sIdentifier
        self.filename = oLine.filename
        self.line_number = oLine.line_number
        self.message = sMessage
        ValueError.__init__(self, f'ERROR: [{sIdentifier}] {self.filename}:{self.line_number} {sMessage}')
