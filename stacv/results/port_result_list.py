
class PortResultList():

    def __init__(self):
        self.results = []

    def add_result(self, oPort):
        self.results.append(oPort)

    def has_failures(self):
        for oPortResult in self.results:
            if oPortResult.has_failures():
                return True
        return False
