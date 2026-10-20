from stacv.rules import rule_result_list


class PortResultList():

    def __init__(self):
        self.results = []

    def add_result(self, oPortResult):
        self.results.append(oPortResult)

    def get_number_of_failures(self):
        return self.get_results().get_number_of_failures()

    def get_number_of_rules(self):
        return self.get_results().get_number_of_rules()

    def get_number_of_skips(self):
        return self.get_results().get_number_of_skips()

    def get_results(self):
        oRuleResults = rule_result_list.RuleResultList()
        for oPortResult in self.results:
            oRuleResults.add_result_list(oPortResult.get_results())
        return oRuleResults

    def has_failures(self):
        for oPortResult in self.results:
            if oPortResult.has_failures():
                return True
        return False
