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
