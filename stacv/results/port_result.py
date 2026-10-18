
class PortResult():

    def __init__(self, oPort, oMethodology):
        self.port = oPort
        self.methodology_results = oMethodology

    def has_failures(self):
        return self.methodology_results.has_failures()
