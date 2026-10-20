
class PortResultList():

    def __init__(self):
        self.results = []

    def add_result(self, oPortResult):
        self.results.append(oPortResult)

    def get_number_of_failures(self):
        iRules = 0
        for oResult in self.results:
            iRules += oResult.get_number_of_failures()
        return iRules

    def get_number_of_rules(self):
        iRules = 0
        for oResult in self.results:
            iRules += oResult.get_number_of_rules()
        return iRules

    def get_number_of_skips(self):
        iRules = 0
        for oResult in self.results:
            iRules += oResult.get_number_of_skips()
        return iRules

    def has_failures(self):
        for oPortResult in self.results:
            if oPortResult.has_failures():
                return True
        return False
