
class StageResults():

    def __init__(self, sName, oRuleResultList):
        self.name = sName
        self.rule_results = oRuleResultList

    def get_failing_results(self):
        return self.rule_results.get_failing_results()

    def get_results(self):
        return self.rule_results

    def has_failures(self):
        return self.rule_results.has_failures()
