
class PortResult():

    def __init__(self, oPort, oMethodologyResults):
        self.port = oPort
        self.methodology_results = oMethodologyResults

    def get_number_of_failures(self):
        return self.methodology_results.get_number_of_failures()

    def get_number_of_rules(self):
        return self.methodology_results.get_number_of_rules()

    def get_number_of_skips(self):
        return self.methodology_results.get_number_of_skips()

    def get_results(self):
        return self.methodology_results.get_results()

    def has_failures(self):
        return self.methodology_results.has_failures()
