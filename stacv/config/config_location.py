'''
Where in an input file a key is, for error messages.
'''

class ConfigLocation():

    def __init__(self, sFilename):
        self.filename = sFilename
        self.location = ''
