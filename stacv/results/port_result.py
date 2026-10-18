
class PortResult():

    def __init__(self, oPort, oMethodologyResults):
        self.port = oPort
        self.methodology_results = oMethodologyResults

    def has_failures(self):
        return self.methodology_results.has_failures()
