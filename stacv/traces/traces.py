
from stacv.config import config_reader
from stacv.config import value_type
from stacv.traces import trace
from stacv.traces import trace_delay
from stacv.traces import trace_list
from stacv.traces import traces_config_error
from stacv.traces import traces_location

READER = config_reader.ConfigReader('traces_config', traces_config_error.TracesConfigError)
TOP_LEVEL_KEYS = ['default_delay', 'trace']
TRACE_KEYS = ['name', 'device_pin', 'part_pin', 'device_to_part', 'part_to_device']
DELAY_KEYS = ['max_delay', 'min_delay']


def create_trace_list(oInterface):
    dTraces = READER.read_toml_file(oInterface.traces)
    return build_trace_list(dTraces, oInterface.traces)


def build_trace_list(dTraces, sFilename):
    oLocation = traces_location.TracesLocation(sFilename)
    READER.check_keys(dTraces, TOP_LEVEL_KEYS, oLocation)
    oDefaultDelay = read_default_delay(dTraces, sFilename)
    oTraceList = trace_list.TraceList()
    oTraceList.traces = build_traces(dTraces, oDefaultDelay, oLocation)
    return oTraceList


def read_default_delay(dTraces, sFilename):
    if 'default_delay' not in dTraces:
        return None
    oLocation = traces_location.TracesLocation(sFilename)
    dDelays = READER.get_required_table(dTraces, 'default_delay', oLocation)
    oLocation.set_default_delay()
    READER.check_keys(dDelays, DELAY_KEYS, oLocation)
    return read_delays(dDelays, True, oLocation)


def read_delays(dDelays, bIsDefault, oLocation):
    fMaxDelay = READER.get_required_number(dDelays, 'max_delay', oLocation)
    fMinDelay = READER.get_required_number(dDelays, 'min_delay', oLocation)
    return trace_delay.TraceDelay(fMaxDelay, fMinDelay, bIsDefault)


def build_traces(dTraces, oDefaultDelay, oLocation):
    lTraces = []
    for iTrace, dTrace in enumerate(READER.get_required_array_of_tables(dTraces, 'trace', oLocation), start=1):
        lTraces.append(build_trace(dTrace, iTrace, oDefaultDelay, oLocation))
    return lTraces


def build_trace(dTrace, iTrace, oDefaultDelay, oLocation):
    set_trace_location(dTrace, iTrace, oLocation)
    READER.check_keys(dTrace, TRACE_KEYS, oLocation)
    oTrace = trace.Trace()
    oTrace.name = READER.get_required_string(dTrace, 'name', oLocation)
    oLocation.set_trace_name(oTrace.name)
    oTrace.device_pin = READER.get_required_string(dTrace, 'device_pin', oLocation)
    oTrace.part_pin = READER.get_required_string(dTrace, 'part_pin', oLocation)
    if 'device_to_part' in dTrace:
        oTrace.device_to_part = build_trace_delay(dTrace, oTrace.name, 'device_to_part', oDefaultDelay, oLocation)
    if 'part_to_device' in dTrace:
        oTrace.part_to_device = build_trace_delay(dTrace, oTrace.name, 'part_to_device', oDefaultDelay, oLocation)
    return oTrace


def set_trace_location(dTrace, iTrace, oLocation):
    # Unknown keys are checked before the name is read, so a trace is named by its name only once the name is valid.
    oLocation.set_trace_number(iTrace)
    if 'name' in dTrace and value_type.STRING.is_valid(dTrace['name']):
        oLocation.set_trace_name(dTrace['name'])


def build_trace_delay(dTrace, sTraceName, sDirection, oDefaultDelay, oLocation):
    dDelays = READER.get_required_table(dTrace, sDirection, oLocation)
    oDelayLocation = traces_location.TracesLocation(oLocation.filename)
    oDelayLocation.set_direction(sDirection, sTraceName)
    READER.check_keys(dDelays, DELAY_KEYS, oDelayLocation)
    if has_no_delays(dDelays):
        return build_default_trace_delay(sTraceName, sDirection, oDefaultDelay, oLocation)
    check_both_delays_are_given(dDelays, sTraceName, sDirection, oLocation)
    return read_delays(dDelays, False, oDelayLocation)


def has_no_delays(dDelays):
    return len(dDelays) == 0


def build_default_trace_delay(sTraceName, sDirection, oDefaultDelay, oLocation):
    if oDefaultDelay is None:
        READER.raise_error(5, oLocation.filename, f'trace {sTraceName} has no delays in key "{sDirection}" and no default_delay is defined')
    # Each trace gets its own delays, so a change to one trace cannot change another.
    return trace_delay.TraceDelay(oDefaultDelay.max_delay, oDefaultDelay.min_delay, True)


def check_both_delays_are_given(dDelays, sTraceName, sDirection, oLocation):
    if 'max_delay' not in dDelays or 'min_delay' not in dDelays:
        READER.raise_error(6, oLocation.filename, f'trace {sTraceName} key "{sDirection}" must give both max_delay and min_delay, or neither')
