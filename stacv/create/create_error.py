'''
Provides error reporting for files that cannot be created.
'''

class CreateError(ValueError):

    def __init__(self, sIdentifier, sMessage):
        self.identifier = sIdentifier
        self.message = sMessage
        ValueError.__init__(self, f'ERROR: [{sIdentifier}] {sMessage}')
