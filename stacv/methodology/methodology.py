from stacv.rules import rule_result_list


class Methodology():

    def __init__(self):
        self.stages = []

    def check(self, oTimingReportList):
        oRuleResults = rule_result_list.RuleResultList()
        sSkipStageReason = None
        for oStage in self.stages:
            if prior_stage_has_failed(sSkipStageReason):
                oRuleResults.add_result_list(oStage.skip(sSkipStageReason))
            else:
                oStageResults = oStage.check(oTimingReportList)
                oRuleResults.add_result_list(oStageResults)
                if oStageResults.has_failures():
                    sSkipStageReason = f'{oStage.name} failed'
        return oRuleResults


def prior_stage_has_failed(sReason):
    return sReason is not None
