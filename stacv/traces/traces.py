
import tomllib

from stacv.traces import trace
from stacv.traces import trace_delay
from stacv.traces import trace_list
from stacv.traces import traces_config_error


def create_trace_list(oInterface):
    dTraces = read_file(oInterface.traces)
    return build_trace_list(dTraces, oInterface.traces)


def read_file(sFilename):
    return read_toml_file(sFilename)


def read_toml_file(sFilename):
    with open(sFilename, 'rb') as oFile:
        return tomllib.load(oFile)


def build_trace_list(dTraces, sFilename):
    oTraceList = trace_list.TraceList()
    oTraceList.traces = build_traces(dTraces, sFilename)
    return oTraceList


def build_traces(dTraces, sFilename):
    dDefaultDelay = get_default_delay(dTraces)
    lTraces = []
    for dTrace in dTraces['trace']:
        oTrace = build_trace(dTrace, dDefaultDelay, sFilename)
        lTraces.append(oTrace)
    return lTraces


def get_default_delay(dTraces):
    if 'default_delay' in dTraces:
        return dTraces['default_delay']
    return None


def build_trace(dTrace, dDefaultDelay, sFilename):
    oTrace = trace.Trace()
    oTrace.name = dTrace['name']
    oTrace.device_pin = dTrace['device_pin']
    oTrace.part_pin = dTrace['part_pin']
    if 'device_to_part' in dTrace:
        oTrace.device_to_part = build_trace_delay(dTrace, 'device_to_part', dDefaultDelay, sFilename)
    if 'part_to_device' in dTrace:
        oTrace.part_to_device = build_trace_delay(dTrace, 'part_to_device', dDefaultDelay, sFilename)
    return oTrace


def build_trace_delay(dTrace, sKey, dDefaultDelay, sFilename):
    dDelays = dTrace[sKey]
    if has_no_delays(dDelays):
        return build_default_trace_delay(dTrace, sKey, dDefaultDelay, sFilename)
    check_both_delays_are_given(dTrace, sKey, sFilename)
    return trace_delay.TraceDelay(dDelays['max_delay'], dDelays['min_delay'], False)


def has_no_delays(dDelays):
    return len(dDelays) == 0


def build_default_trace_delay(dTrace, sKey, dDefaultDelay, sFilename):
    if dDefaultDelay is None:
        raise traces_config_error.TracesConfigError('traces_config_001', sFilename, f'trace {dTrace["name"]} has no delays in key "{sKey}" and no default_delay is defined')
    return trace_delay.TraceDelay(dDefaultDelay['max_delay'], dDefaultDelay['min_delay'], True)


def check_both_delays_are_given(dTrace, sKey, sFilename):
    dDelays = dTrace[sKey]
    if 'max_delay' not in dDelays or 'min_delay' not in dDelays:
        raise traces_config_error.TracesConfigError('traces_config_002', sFilename, f'trace {dTrace["name"]} key "{sKey}" must give both max_delay and min_delay, or neither')
