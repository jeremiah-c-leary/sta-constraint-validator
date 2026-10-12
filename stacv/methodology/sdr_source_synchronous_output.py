from stacv.methodology import methodology
from stacv.methodology import stage

from stacv.rules.clock import s1_clock_001, s2_clock_001, s2_clock_002
from stacv.rules.timing_report import s0_timing_report_001, s0_timing_report_002
from stacv.rules.data_path import s2_data_path_001
from stacv.rules.output_delay import s2_output_delay_001, s2_output_delay_002


class SdrSourceSynchronousOutput(methodology.Methodology):

    def __init__(self):
        self.stages = []
        self.stages.append(stage.Stage('stage 0', [s0_timing_report_001, s0_timing_report_002]))
        self.stages.append(stage.Stage('stage 1', [s1_clock_001]))
        self.stages.append(stage.Stage('stage 2', [s2_clock_001, s2_clock_002, s2_data_path_001, s2_output_delay_001, s2_output_delay_002]))
