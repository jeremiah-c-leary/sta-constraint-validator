
from stacv.results import methodology_results

# Which way the data goes between the device and the part.
OUTPUT = 'output'
INPUT = 'input'
# The key of the port clock that the device forwards to the part.
CAPTURE_CLOCK = 'capture_clock'
LAUNCH_CLOCK = 'launch_clock'


def describe_clock_key(sClockKey):
    # The key launch_clock is described as the launch clock.
    return sClockKey.replace('_', ' ')


class Methodology():

    def __init__(self):
        self.stages = []
        self.data_direction = OUTPUT
        self.forwarded_clock_key = CAPTURE_CLOCK

    def has_rules(self):
        return len(self.stages) > 0

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
