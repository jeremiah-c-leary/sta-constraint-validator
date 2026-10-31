'''
Provides error reporting for traces file issues.
'''

class TracesConfigError(ValueError):

    def __init__(self, sIdentifier, sTracesFile, sMessage):
        self.identifier = sIdentifier
        self.message = sMessage
        ValueError.__init__(self, f'ERROR: [{sIdentifier}] {sTracesFile} {sMessage}')
