ANALYZE = 'analyze'
DEFER = 'defer'


class Port():
    def __init__(self):
        self.name = None
        self.status = ANALYZE
        self.methodology = None
        self.capture_clock = None
        self.launch_clock = None
        # The port clock the device forwards to the part: the capture clock of an output, the launch clock of a round trip.
        self.forwarded_clock = None
        self.forwarded_clock_key = None
        # Whether the device sends the data to the part, or receives it.
        self.data_direction = None
        self.clock_origin = None
        self.part_pin_methodology = None
        self.double_data_rate = False
        self.timing_reports = []
        # As written in the interface file, before environment variables are expanded.
        self.timing_reports_as_written = []
        # Errors in the edges, which stacv visualize edges draws and every other command stops on.
        self.edge_errors = []
