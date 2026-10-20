from stacv.results import rule_result_list


class MethodologyResults():

    def __init__(self):
        self.stage_results = []

    def add_stage_result(self, oStageResult):
        self.stage_results.append(oStageResult)

    def get_failing_results(self):
        lFailingResults = []
        for oStageResult in self.stage_results:
            if oStageResult.has_failures():
                lFailingResults.extend(oStageResult.get_failing_results())
        return lFailingResults

    def get_results(self):
        oRuleResults = rule_result_list.RuleResultList()
        for oStageResult in self.stage_results:
            oRuleResults.add_result_list(oStageResult.get_results())
        return oRuleResults

    def has_failures(self):
        for oStageResult in self.stage_results:
            if oStageResult.has_failures():
                return True
        return False
