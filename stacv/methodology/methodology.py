
from stacv.results import methodology_results


class Methodology():

    def __init__(self):
        self.stages = []

    def check(self, oPortProfile):
        oMethodologyResults = methodology_results.MethodologyResults()
        sSkipStageReason = None
        for oStage in self.stages:
            if prior_stage_has_failed(sSkipStageReason):
                oStageResults = oStage.skip(sSkipStageReason)
            else:
                oStageResults = oStage.check(oPortProfile)
                if oStageResults.has_failures():
                    sSkipStageReason = f'{oStage.name} failed'
            oMethodologyResults.add_stage_result(oStageResults)
        return oMethodologyResults


def prior_stage_has_failed(sReason):
    return sReason is not None
