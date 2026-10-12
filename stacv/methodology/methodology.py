from stacv.rules import rule_result_list


class Methodology():

    def __init__(self):
        self.stages = []

    def check(self, oTimingReportList):
        oRuleResults = rule_result_list.RuleResultList()
        sSkipStageReason = None
        for oStage in self.stages:
            if sSkipStageReason is not None:
                oRuleResults.add_result_list(oStage.skip(sSkipStageReason))
            if sSkipStageReason is None:
                oRuleResults.add_result_list(oStage.check(oTimingReportList))
                if oRuleResults.has_failures():
                    sSkipStageReason = f'{oStage.name} failed'
        return oRuleResults
