
class TimingReportParseError(ValueError):

    def __init__(self, sIdentifier, sFilename, iLineNumber, sMessage):
        self.identifier = sIdentifier
        self.filename = sFilename
        self.lineNumber = iLineNumber
        self.message = sMessage
        ValueError.__init__(self, f'ERROR: [{sIdentifier}] {sFilename}:{iLineNumber} {sMessage}')
