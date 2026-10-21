
import tomllib

from stacv.traces import trace
from stacv.traces import trace_delay
from stacv.traces import trace_list


def create_trace_list(oInterface):
    dTraces = read_file(oInterface.traces)
    return build_trace_list(dTraces)


def read_file(sFilename):
    return read_toml_file(sFilename)


def read_toml_file(sFilename):
    with open(sFilename, 'rb') as oFile:
        return tomllib.load(oFile)


def build_trace_list(dTraces):
    oTraceList = trace_list.TraceList()
    oTraceList.traces = build_traces(dTraces)
    return oTraceList


def build_traces(dTraces):
    lTraces = []
    for dTrace in dTraces['trace']:
        oTrace = build_trace(dTrace)
        lTraces.append(oTrace)
    return lTraces


def build_trace(dTrace):
    oTrace = trace.Trace()
    oTrace.name = dTrace['name']
    oTrace.device_pin = dTrace['device_pin']
    oTrace.part_pin = dTrace['part_pin']
    if 'device_to_part' in dTrace:
        oTrace.device_to_part = build_trace_delay(dTrace['device_to_part'])
    if 'part_to_device' in dTrace:
        oTrace.part_to_device = build_trace_delay(dTrace['part_to_device'])
    return oTrace


def build_trace_delay(dDelays):
    return trace_delay.TraceDelay(dDelays['max_delay'], dDelays['min_delay'])
