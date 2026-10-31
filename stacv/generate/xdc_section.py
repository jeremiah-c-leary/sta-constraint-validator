
class Section():

    def __init__(self, sNumber, sTitle, lContent):
        self.number = sNumber
        self.title = sTitle
        self.content = lContent

    def has_subsections(self):
        return self.content is None
