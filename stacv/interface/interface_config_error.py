'''
Provides error reporting for configuration issues.
'''

class InterfaceConfigError(ValueError):

    def __init__(self, sIdentifier, sInterfaceFile, sMessage):
        self.identifier = sIdentifier
        self.message = sMessage
        ValueError.__init__(self, f'ERROR: [{sIdentifier}] {sInterfaceFile} {sMessage}')
