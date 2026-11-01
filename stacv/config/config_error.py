'''
The error of an input file that stacv cannot read.
'''

class ConfigError(ValueError):

    def __init__(self, sIdentifier, sFilename, sMessage):
        self.identifier = sIdentifier
        self.message = sMessage
        ValueError.__init__(self, f'ERROR: [{sIdentifier}] {sFilename} {sMessage}')
