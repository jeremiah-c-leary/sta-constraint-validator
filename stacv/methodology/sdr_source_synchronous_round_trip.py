from stacv.methodology import methodology
from stacv.methodology import stage

from stacv.rules.clock import s0_clock_path_002
from stacv.rules.clock import s1_clock_001
from stacv.rules.clock import s2_clock_001
from stacv.rules.clock import s2_clock_002
from stacv.rules.clock import s4_capture_clock_001
from stacv.rules.clock import s4_capture_clock_002
from stacv.rules.clock import s4_launch_clock_001
from stacv.rules.clock import s4_launch_clock_002
from stacv.rules.data_path import s0_data_path_002
from stacv.rules.data_path import s2_data_path_001
from stacv.rules.input_delay import s2_input_delay_001
from stacv.rules.input_delay import s2_input_delay_002
from stacv.rules.input_delay import s3_input_delay_001
from stacv.rules.input_delay import s3_input_delay_002
from stacv.rules.part import s4_part_002
from stacv.rules.requirement import s4_requirement_001
from stacv.rules.requirement import s4_requirement_002
from stacv.rules.slack import s5_slack_001
from stacv.rules.slack import s5_slack_002
from stacv.rules.timing_report import s0_timing_report_001
from stacv.rules.timing_report import s0_timing_report_002
from stacv.rules.trace import s0_trace_001
from stacv.visualize import edges


class SdrSourceSynchronousRoundTrip(methodology.Methodology):
    '''
    Times data the part launches on a clock the device forwards to it, and the device captures with its own clock.
    The launch clock is the forwarded clock, so the timing report runs:
    launch clock path to the clock port -> input delay -> data port -> capture register.
    '''

    def __init__(self):
        methodology.Methodology.__init__(self)
        self.edge_diagram_type = edges.CONTINUOUS_CLOCK
        self.data_direction = methodology.INPUT
        self.forwarded_clock_key = methodology.LAUNCH_CLOCK
        self.part_pin_methodology = 'SDR-SS-RT-DO'
        self.stages.append(stage.Stage('stage 0', [s0_timing_report_001, s0_timing_report_002, s0_trace_001, s0_data_path_002, s0_clock_path_002]))
        self.stages.append(stage.Stage('stage 1', [s1_clock_001]))
        self.stages.append(stage.Stage('stage 2', [s2_clock_001, s2_clock_002, s2_data_path_001, s2_input_delay_001, s2_input_delay_002]))
        self.stages.append(stage.Stage('stage 3', [s3_input_delay_001, s3_input_delay_002]))
        self.stages.append(stage.Stage('stage 4', [s4_capture_clock_001, s4_capture_clock_002, s4_launch_clock_001, s4_launch_clock_002, s4_part_002, s4_requirement_001, s4_requirement_002]))
        self.stages.append(stage.Stage('stage 5', [s5_slack_001, s5_slack_002]))
