'''
Provides error reporting for constraints that cannot be generated.
'''

class GenerateError(ValueError):

    def __init__(self, sIdentifier, sPortName, sMessage):
        self.identifier = sIdentifier
        self.message = sMessage
        ValueError.__init__(self, f'ERROR: [{sIdentifier}] port {sPortName} {sMessage}')
