from stacv.rules import rule_result_list


class Stage():

    def __init__(self, sName, lRules):
        self.name = sName
        self.rules = lRules

    def check(self, oTimingReportList):
        oRuleResults = rule_result_list.RuleResultList()
        for mRule in self.rules:
            oRuleResults.add_result(mRule.check(oTimingReportList))
        return oRuleResults
