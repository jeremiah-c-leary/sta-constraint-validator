
class TimingReportParseError(ValueError):

    def __init__(self, sIdentifier, oTimingReportFile, iLocation, sMessage):
        self.identifier = sIdentifier
        self.filename = oTimingReportFile.filename
        self.location = iLocation
        self.message = sMessage
        ValueError.__init__(self, f'ERROR: [{sIdentifier}] {self.filename}:{iLocation} {sMessage}')
