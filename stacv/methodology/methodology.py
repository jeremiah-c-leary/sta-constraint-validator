from stacv.rules import rule_result_list


class Methodology():

    def __init__(self):
        self.stages = []

    def check(self, oTimingReportList):
        oMethodologyResults = MethodologyResults()
        sSkipStageReason = None
        for oStage in self.stages:
            if prior_stage_has_failed(sSkipStageReason):
                oStageResults = oStage.skip(sSkipStageReason)
            else:
                oStageResults = oStage.check(oTimingReportList)
                if oStageResults.has_failures():
                    sSkipStageReason = f'{oStage.name} failed'
            oMethodologyResults.add_stage_results(oStageResults)
        return oMethodologyResults


def prior_stage_has_failed(sReason):
    return sReason is not None


class MethodologyResults():

    def __init__(self):
        self.stage_results = []

    def add_stage_results(self, oStageResult):
        self.stage_results.append(oStageResult)

    def stage_results(self):
        return self.stages

    def has_failures(self):
        for oStage in self.stage_results:
            if oStage.has_failures():
                return True
        return False

    def get_failing_results(self):
        for oStage in self.stage_results:
            if oStage.has_failures():
                return oStage.get_failing_results()
        return []
