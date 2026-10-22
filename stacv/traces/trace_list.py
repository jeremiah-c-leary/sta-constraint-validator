
class TraceList():

    def __init__(self):
        self.traces = None

    def get_trace_with_device_pin(self, sPinName):
        for oTrace in self.traces:
            if oTrace.device_pin == sPinName:
                return oTrace
        return None

    def get_trace_with_part_pin(self, sPinName):
        for oTrace in self.traces:
            if oTrace.part_pin == sPinName:
                return oTrace
        return None
