
class RuleResultList():

    def __init__(self):
        self.results = []

    def all_passed(self):
        bPassed = None
        for oResult in self.results:
            if not oResult.passed:
                return False
        return True
        

    def add(self, oResult):
        self.results.append(oResult)
