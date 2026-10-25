
class TextRow():

    def __init__(self):
        self.characters = []

    def write(self, iColumn, sText):
        self.extend_to(iColumn + len(sText))
        for iOffset, sCharacter in enumerate(sText):
            self.characters[iColumn + iOffset] = sCharacter

    def extend_to(self, iLength):
        while len(self.characters) < iLength:
            self.characters.append(' ')

    def is_empty(self):
        return self.to_string() == ''

    def to_string(self):
        return ''.join(self.characters).rstrip()
