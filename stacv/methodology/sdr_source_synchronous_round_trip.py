from stacv.methodology import methodology
from stacv.visualize import edges


class SdrSourceSynchronousRoundTrip(methodology.Methodology):
    '''
    Times data the part launches on a clock the device forwards to it, and the device captures with its own clock.
    The launch clock is the forwarded clock, so the round trip starts where the clock leaves the device.
    It has no rules yet, so stacv check defers its ports.
    '''

    def __init__(self):
        methodology.Methodology.__init__(self)
        self.edge_diagram_type = edges.CONTINUOUS_CLOCK
        self.data_direction = methodology.INPUT
        self.forwarded_clock_key = methodology.LAUNCH_CLOCK
