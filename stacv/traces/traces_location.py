from stacv.config import config_location


class TracesLocation(config_location.ConfigLocation):

    def set_trace_number(self, iNumber):
        self.location = f' in trace number {iNumber}'

    def set_trace_name(self, sName):
        self.location = f' in trace {sName}'

    def set_default_delay(self):
        self.location = ' in default_delay'

    def set_direction(self, sDirection, sTraceName):
        self.location = f' in {sDirection} of trace {sTraceName}'
