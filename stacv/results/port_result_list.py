
class PortResultList():

    def __init__(self):
        self.results = []

    def add_result(self, oPortResult):
        self.results.append(oPortResult)

    def has_failures(self):
        for oPortResult in self.results:
            if oPortResult.has_failures():
                return True
        return False
