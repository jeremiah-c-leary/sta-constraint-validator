
class TraceList():

    def __init__(self):
        self.traces = []

    def get_device_to_part_trace_between(self, sDevicePinName, sPartPinName):
        lTraces = self.get_device_to_part_traces()
        for oTrace in lTraces:
            if oTrace.device_pin == sDevicePinName and oTrace.part_pin == sPartPinName:
                return oTrace
        return None

    def get_device_to_part_trace_starting_with_name(self, sName):
        lTraces = self.get_device_to_part_traces()
        for oTrace in lTraces:
            if oTrace.device_pin == sName:
                return oTrace
        return None

    def get_device_to_part_trace_ending_with_name(self, sName):
        lTraces = self.get_device_to_part_traces()
        for oTrace in lTraces:
            if oTrace.part_pin == sName:
                return oTrace
        return None

    def get_device_to_part_traces(self):
        lTraces = []
        for oTrace in self.traces:
            if oTrace.device_to_part is not None:
                lTraces.append(oTrace)
        return lTraces

    def trace_starts_with_device_pin_named(self, sPinName):
        for oTrace in self.get_device_to_part_traces():
            if oTrace.device_pin == sPinName:
                return True
        return False

    def trace_ends_with_part_pin_named(self, sPinName):
        for oTrace in self.get_device_to_part_traces():
            if oTrace.part_pin == sPinName:
                return True
        return False
