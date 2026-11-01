from stacv.methodology import sdr_source_synchronous_output
from stacv.visualize import edges


class SdrSourceSynchronousOutputFirstLastClock(sdr_source_synchronous_output.SdrSourceSynchronousOutput):
    '''
    Times a port to the first and last edges of a clock that stops, such as a chip select.
    The timing tool assumes every clock runs, so the checks are the SDR-SS-O checks;
    only the edge drawing differs.
    '''

    def __init__(self):
        sdr_source_synchronous_output.SdrSourceSynchronousOutput.__init__(self)
        self.edge_diagram_type = edges.FIRST_LAST_CLOCK
