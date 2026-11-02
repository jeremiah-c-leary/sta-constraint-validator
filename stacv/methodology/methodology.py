
from stacv.results import methodology_results

# Which way the data goes between the device and the part.
OUTPUT = 'output'
INPUT = 'input'
# The key of the port clock that crosses the board, between the device's clock port and the part.
CAPTURE_CLOCK = 'capture_clock'
LAUNCH_CLOCK = 'launch_clock'
# Where that clock comes from: the device forwards it, the part sends it, or a clock source drives both.
DEVICE_CLOCK = 'device'
PART_CLOCK = 'part'
SOURCE_CLOCK = 'source'


def describe_clock_key(sClockKey):
    # The key launch_clock is described as the launch clock.
    return sClockKey.replace('_', ' ')


class Methodology():

    def __init__(self):
        self.stages = []
        self.data_direction = OUTPUT
        self.forwarded_clock_key = CAPTURE_CLOCK
        self.clock_origin = DEVICE_CLOCK
        # The methodology of the part pin, from the part's view.
        self.part_pin_methodology = 'SDR-SS-I'
        # A double data rate port changes its data on both edges of the clock.
        self.double_data_rate = False

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
