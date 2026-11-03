from stacv.methodology import methodology
from stacv.methodology import stage

from stacv.rules.clock import s0_clock_path_001
from stacv.rules.clock import s1_clock_001
from stacv.rules.clock import s2_clock_001
from stacv.rules.clock import s2_clock_002
from stacv.rules.clock import s4_capture_clock_001
from stacv.rules.clock import s4_capture_clock_002
from stacv.rules.clock import s4_launch_clock_001
from stacv.rules.clock import s4_launch_clock_002
from stacv.rules.data_path import s0_data_path_001
from stacv.rules.output_delay import s2_output_delay_001
from stacv.rules.output_delay import s2_output_delay_002
from stacv.rules.output_delay import s3_output_delay_001
from stacv.rules.output_delay import s3_output_delay_002
from stacv.rules.register import s0_register_001
from stacv.rules.register import s0_register_002
from stacv.rules.register import s0_register_003
from stacv.rules.part import s4_part_001
from stacv.rules.requirement import s4_requirement_001
from stacv.rules.requirement import s4_requirement_002
from stacv.rules.slack import s5_slack_001
from stacv.rules.slack import s5_slack_002
from stacv.rules.timing_report import s0_timing_report_001
from stacv.rules.timing_report import s0_timing_report_002
from stacv.rules.trace import s0_trace_001
from stacv.visualize import edges


class SdrSourceSynchronousOutput(methodology.Methodology):

    def __init__(self):
        methodology.Methodology.__init__(self)
        self.edge_diagram_type = edges.CONTINUOUS_CLOCK
        self.stages.append(stage.Stage('stage 0', [s0_timing_report_001, s0_timing_report_002, s0_trace_001, s0_data_path_001, s0_clock_path_001, s0_register_001, s0_register_002, s0_register_003]))
        self.stages.append(stage.Stage('stage 1', [s1_clock_001]))
        self.stages.append(stage.Stage('stage 2', [s2_clock_001, s2_clock_002, s2_output_delay_001, s2_output_delay_002]))
        self.stages.append(stage.Stage('stage 3', [s3_output_delay_001, s3_output_delay_002]))
        self.stages.append(stage.Stage('stage 4', [s4_capture_clock_001, s4_capture_clock_002, s4_launch_clock_001, s4_launch_clock_002, s4_part_001, s4_requirement_001, s4_requirement_002]))
        self.stages.append(stage.Stage('stage 5', [s5_slack_001, s5_slack_002]))
