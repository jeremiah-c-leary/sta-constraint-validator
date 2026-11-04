'''
The methodologies stacv generates constraints for, but has no rules for yet.
Each one says which way its data goes, which clock crosses the board and where that clock comes from.
'''

from stacv.methodology import methodology
from stacv.visualize import edges


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


class SdrSourceSynchronousRoundTripDataOut(methodology.Methodology):
    '''
    The part sends a clock, the device launches its data on that clock, and the part captures the data on it.
    '''

    def __init__(self):
        methodology.Methodology.__init__(self)
        self.edge_diagram_type = edges.CONTINUOUS_CLOCK
        self.data_direction = methodology.OUTPUT
        self.forwarded_clock_key = methodology.LAUNCH_CLOCK
        self.clock_origin = methodology.PART_CLOCK
        self.part_pin_methodology = 'SDR-SS-RT-DI'


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
