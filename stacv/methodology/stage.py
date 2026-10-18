from stacv.rules import rule_result
from stacv.rules import rule_result_list


class Stage():

    def __init__(self, sName, lRules):
        self.name = sName
        self.rules = lRules

    def check(self, oTimingReportList):
        oRuleResults = rule_result_list.RuleResultList()
        for mRule in self.rules:
            oRuleResults.add_result(mRule.check(oTimingReportList))
        return StageResults(self.name, oRuleResults)

    def skip(self, sReason):
        oRuleResults = rule_result_list.RuleResultList()
        for mRule in self.rules:
            lDetail = [sReason]
            oRuleResult = rule_result.RuleResult(mRule.RULE_ID, rule_result.SKIPPED, lDetail)
            oRuleResults.add_result(oRuleResult)
        return StageResults(self.name, oRuleResults)


class StageResults():

    def __init__(self, sName, oRuleResultsList):
        self.name = sName
        self.rule_results = oRuleResultsList

    def get_failing_results(self):
        return self.rule_results.get_failing_results()

    def has_failures(self):
        return self.rule_results.has_failures()
