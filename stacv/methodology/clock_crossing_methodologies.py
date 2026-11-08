'''
The methodologies whose clock comes from the part or a clock source, and the double data rate methodologies.
Each one says which way its data goes, which clock crosses the board and where that clock comes from,
and runs the shared rules with the delay calculation of its own.
'''

from stacv.methodology import methodology
from stacv.methodology import stage
from stacv.rules.clock import s0_clock_path_001
from stacv.rules.clock import s0_clock_path_003
from stacv.rules.clock import s1_clock_001
from stacv.rules.clock import s2_clock_001
from stacv.rules.clock import s2_clock_002
from stacv.rules.clock import s4_capture_clock_001
from stacv.rules.clock import s4_capture_clock_002
from stacv.rules.clock import s4_launch_clock_001
from stacv.rules.clock import s4_launch_clock_002
from stacv.rules.data_path import s0_data_path_001
from stacv.rules.data_path import s0_data_path_002
from stacv.rules.edge import s4_edge_001
from stacv.rules.edge import s4_edge_002
from stacv.rules.input_delay import s2_input_delay_001
from stacv.rules.input_delay import s2_input_delay_002
from stacv.rules.input_delay import s3_input_delay_003
from stacv.rules.input_delay import s3_input_delay_004
from stacv.rules.input_delay import s3_input_delay_005
from stacv.rules.input_delay import s3_input_delay_006
from stacv.rules.output_delay import s2_output_delay_001
from stacv.rules.output_delay import s2_output_delay_002
from stacv.rules.output_delay import s3_output_delay_001
from stacv.rules.output_delay import s3_output_delay_002
from stacv.rules.output_delay import s3_output_delay_003
from stacv.rules.output_delay import s3_output_delay_004
from stacv.rules.output_delay import s3_output_delay_005
from stacv.rules.output_delay import s3_output_delay_006
from stacv.rules.part import s4_part_001
from stacv.rules.part import s4_part_002
from stacv.rules.register import s0_register_001
from stacv.rules.register import s0_register_002
from stacv.rules.register import s0_register_003
from stacv.rules.requirement import s4_requirement_001
from stacv.rules.requirement import s4_requirement_002
from stacv.rules.slack import s5_slack_001
from stacv.rules.slack import s5_slack_002
from stacv.rules.timing_report import s0_timing_report_001
from stacv.rules.timing_report import s0_timing_report_002
from stacv.rules.trace import s0_trace_001
from stacv.visualize import edges

# The rules every methodology runs in each stage, with the rules of its own added.
SHARED_STAGE_0 = [s0_timing_report_001, s0_timing_report_002, s0_trace_001, s0_register_001, s0_register_002, s0_register_003]
SHARED_STAGE_2 = [s2_clock_001, s2_clock_002]
SHARED_STAGE_4 = [s4_capture_clock_001, s4_capture_clock_002, s4_launch_clock_001, s4_launch_clock_002, s4_requirement_001, s4_requirement_002]


def add_stages(oMethodology, lStage0, lStage2, lStage3, lStage4):
    oMethodology.stages.append(stage.Stage('stage 0', SHARED_STAGE_0 + lStage0))
    oMethodology.stages.append(stage.Stage('stage 1', [s1_clock_001]))
    oMethodology.stages.append(stage.Stage('stage 2', SHARED_STAGE_2 + lStage2))
    oMethodology.stages.append(stage.Stage('stage 3', lStage3))
    oMethodology.stages.append(stage.Stage('stage 4', SHARED_STAGE_4 + lStage4))
    oMethodology.stages.append(stage.Stage('stage 5', [s5_slack_001, s5_slack_002]))


def add_input_stages(oMethodology, lStage3, lStage4):
    # The data path starts at the port, and the clock from the part or the source enters on the clock port.
    add_stages(oMethodology, [s0_data_path_002, s0_clock_path_003], [s2_input_delay_001, s2_input_delay_002], lStage3, [s4_part_002] + lStage4)


def add_output_stages(oMethodology, lStage0, lStage3, lStage4):
    add_stages(oMethodology, [s0_data_path_001] + lStage0, [s2_output_delay_001, s2_output_delay_002], lStage3, [s4_part_001] + lStage4)


class SdrSourceSynchronousInput(methodology.Methodology):
    '''
    The part sends its clock with the data, and the device captures the data on that clock.
    '''

    def __init__(self):
        methodology.Methodology.__init__(self)
        self.edge_diagram_type = edges.CONTINUOUS_CLOCK
        self.data_direction = methodology.INPUT
        self.forwarded_clock_key = methodology.LAUNCH_CLOCK
        self.clock_origin = methodology.PART_CLOCK
        self.part_pin_methodology = 'SDR-SS-O'
        add_input_stages(self, [s3_input_delay_003, s3_input_delay_004], [])


class SdrSourceSynchronousRoundTripDataOut(methodology.Methodology):
    '''
    The device launches its data on a clock it receives from the part, and the part captures the data on that clock.
    '''

    def __init__(self):
        methodology.Methodology.__init__(self)
        self.edge_diagram_type = edges.CONTINUOUS_CLOCK
        self.data_direction = methodology.OUTPUT
        self.forwarded_clock_key = methodology.LAUNCH_CLOCK
        self.clock_origin = methodology.PART_CLOCK
        self.part_pin_methodology = 'SDR-SS-RT-DI'
        add_output_stages(self, [s0_clock_path_003], [s3_output_delay_003, s3_output_delay_004], [])


class SdrSystemSynchronousOutput(methodology.Methodology):
    '''
    A clock source drives the device and the part, and the device sends data the part captures.
    '''

    def __init__(self):
        methodology.Methodology.__init__(self)
        self.edge_diagram_type = edges.CONTINUOUS_CLOCK
        self.data_direction = methodology.OUTPUT
        self.forwarded_clock_key = methodology.LAUNCH_CLOCK
        self.clock_origin = methodology.SOURCE_CLOCK
        self.part_pin_methodology = 'SDR-SYS-I'
        add_output_stages(self, [s0_clock_path_003], [s3_output_delay_005, s3_output_delay_006], [])


class SdrSystemSynchronousInput(methodology.Methodology):
    '''
    A clock source drives the device and the part, and the part sends data the device captures.
    '''

    def __init__(self):
        methodology.Methodology.__init__(self)
        self.edge_diagram_type = edges.CONTINUOUS_CLOCK
        self.data_direction = methodology.INPUT
        self.forwarded_clock_key = methodology.LAUNCH_CLOCK
        self.clock_origin = methodology.SOURCE_CLOCK
        self.part_pin_methodology = 'SDR-SYS-O'
        add_input_stages(self, [s3_input_delay_005, s3_input_delay_006], [])


class DdrSourceSynchronousOutput(methodology.Methodology):
    '''
    The device forwards a clock and sends data the part captures on both of its edges.
    '''

    def __init__(self):
        methodology.Methodology.__init__(self)
        self.edge_diagram_type = edges.CONTINUOUS_CLOCK
        self.data_direction = methodology.OUTPUT
        self.forwarded_clock_key = methodology.CAPTURE_CLOCK
        self.clock_origin = methodology.DEVICE_CLOCK
        self.part_pin_methodology = 'DDR-SS-I'
        self.double_data_rate = True
        # The device forwards the clock, so the capture clock path ends at the clock port, as for SDR-SS-O.
        add_output_stages(self, [s0_clock_path_001], [s3_output_delay_001, s3_output_delay_002], [s4_edge_001])


class DdrSourceSynchronousInput(methodology.Methodology):
    '''
    The part sends its clock with data that changes on both of its edges, and the device captures it on that clock.
    Which edge captures each bit is the device's choice, and each choice is its own methodology.
    '''

    def __init__(self):
        methodology.Methodology.__init__(self)
        self.edge_diagram_type = edges.CONTINUOUS_CLOCK
        self.data_direction = methodology.INPUT
        self.forwarded_clock_key = methodology.LAUNCH_CLOCK
        self.clock_origin = methodology.PART_CLOCK
        self.part_pin_methodology = 'DDR-SS-O'
        self.double_data_rate = True
        add_input_stages(self, [s3_input_delay_003, s3_input_delay_004], [s4_edge_001, s4_edge_002])


class DdrSourceSynchronousInputSameEdge(DdrSourceSynchronousInput):
    '''
    Each edge captures the data it is aligned with, after the clock's delay into the device.
    '''

    def __init__(self):
        DdrSourceSynchronousInput.__init__(self)
        self.setup_capture_edges_after_launch = 0
        self.capture_edge_description = 'a DDR-SS-I-SE port captures each bit on the edge it is aligned with'


class DdrSourceSynchronousInputNextEdge(DdrSourceSynchronousInput):
    '''
    Each edge captures the data the edge before it launched.
    '''

    def __init__(self):
        DdrSourceSynchronousInput.__init__(self)
        self.setup_capture_edges_after_launch = 1
        self.capture_edge_description = 'a DDR-SS-I-NE port captures each bit on the edge after the one it is launched on'
