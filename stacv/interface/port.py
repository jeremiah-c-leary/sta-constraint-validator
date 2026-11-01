ANALYZE = 'analyze'
DEFER = 'defer'


class Port():
    def __init__(self):
        self.name = None
        self.status = ANALYZE
        self.methodology = None
        self.capture_clock = None
        self.launch_clock = None
        self.timing_reports = []
        # As written in the interface file, before environment variables are expanded.
        self.timing_reports_as_written = []
        # Errors in the edges, which stacv visualize edges draws and every other command stops on.
        self.edge_errors = []
