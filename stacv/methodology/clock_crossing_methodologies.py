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
    '''

    def __init__(self):
        methodology.Methodology.__init__(self)
        self.edge_diagram_type = edges.CONTINUOUS_CLOCK
        self.data_direction = methodology.INPUT
        self.forwarded_clock_key = methodology.LAUNCH_CLOCK
        self.clock_origin = methodology.PART_CLOCK
        self.part_pin_methodology = 'DDR-SS-O'
        self.double_data_rate = True
