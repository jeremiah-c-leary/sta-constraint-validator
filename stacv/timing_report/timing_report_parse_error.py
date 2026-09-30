
class TimingReportParseError(ValueError):

    def __init__(self, sIdentifier, sFilename, iLocation, sMessage):
        self.identifier = sIdentifier
        self.filename = sFilename
        self.location = iLocation
        self.message = sMessage
        ValueError.__init__(self, f'ERROR: [{sIdentifier}] {sFilename}:{iLocation} {sMessage}')
