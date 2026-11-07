
from stacv.config import config_reader
from stacv.config import value_type
from stacv.traces import trace
from stacv.traces import trace_delay
from stacv.traces import trace_list
from stacv.traces import traces_config_error
from stacv.traces import traces_location

READER = config_reader.ConfigReader('traces_config', traces_config_error.TracesConfigError)
TOP_LEVEL_KEYS = ['default_delay', 'trace']
TRACE_KEYS = ['name', 'if_signal', 'device_pin', 'part_pin', 'device_to_part', 'part_to_device', 'source', 'source_to_device', 'source_to_part']
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
    return read_delays(dDelays, True, 'default_delay', oLocation)


def read_delays(dDelays, bIsDefault, sDescription, oLocation):
    fMaxDelay = READER.get_required_number(dDelays, 'max_delay', oLocation)
    fMinDelay = READER.get_required_number(dDelays, 'min_delay', oLocation)
    if fMaxDelay < fMinDelay:
        READER.raise_error(8, oLocation.filename, f'{sDescription} has max_delay {fMaxDelay} less than min_delay {fMinDelay}')
    return trace_delay.TraceDelay(fMaxDelay, fMinDelay, bIsDefault)


def build_traces(dTraces, oDefaultDelay, oLocation):
    lTraces = []
    lNames = []
    for iTrace, dTrace in enumerate(READER.get_required_array_of_tables(dTraces, 'trace', oLocation), start=1):
        oTrace = build_trace(dTrace, iTrace, oDefaultDelay, oLocation)
        check_trace_is_not_defined(lNames, oTrace.name, oLocation)
        lTraces.append(oTrace)
    return lTraces


def check_trace_is_not_defined(lNames, sName, oLocation):
    if sName in lNames:
        READER.raise_error(9, oLocation.filename, f'trace {sName} is defined by more than one [[trace]] table')
    lNames.append(sName)


def build_trace(dTrace, iTrace, oDefaultDelay, oLocation):
    set_trace_location(dTrace, iTrace, oLocation)
    READER.check_keys(dTrace, TRACE_KEYS, oLocation)
    oTrace = trace.Trace()
    oTrace.name = READER.get_required_string(dTrace, 'name', oLocation)
    oLocation.set_trace_name(oTrace.name)
    if 'source' in dTrace:
        check_source_trace_has_no_signal(dTrace, oTrace.name, oLocation)
        return build_source_trace(dTrace, oTrace, oDefaultDelay, oLocation)
    read_trace_ends(dTrace, oTrace, oLocation)
    if 'device_to_part' in dTrace:
        oTrace.device_to_part = build_trace_delay(dTrace, oTrace.name, 'device_to_part', oDefaultDelay, oLocation)
    if 'part_to_device' in dTrace:
        oTrace.part_to_device = build_trace_delay(dTrace, oTrace.name, 'part_to_device', oDefaultDelay, oLocation)
    if oTrace.device_to_part is None and oTrace.part_to_device is None:
        READER.raise_error(7, oLocation.filename, f'trace {oTrace.name} has neither device_to_part nor part_to_device')
    return oTrace


def read_trace_ends(dTrace, oTrace, oLocation):
    # A trace names its ends, or the signal of the interface standard it carries, which names them; not both.
    bHasPins = 'device_pin' in dTrace or 'part_pin' in dTrace
    if 'if_signal' in dTrace and bHasPins:
        READER.raise_error(11, oLocation.filename, f'trace {oTrace.name} gives if_signal and a pin; give if_signal, or device_pin and part_pin')
    if 'if_signal' in dTrace:
        oTrace.if_signal = READER.get_required_string(dTrace, 'if_signal', oLocation)
        return
    oTrace.device_pin = READER.get_required_string(dTrace, 'device_pin', oLocation)
    oTrace.part_pin = READER.get_required_string(dTrace, 'part_pin', oLocation)


def check_source_trace_has_no_signal(dTrace, sTraceName, oLocation):
    if 'if_signal' in dTrace:
        READER.raise_error(11, oLocation.filename, f'trace {sTraceName} from a clock source gives if_signal; a trace from a clock source names its pin')


def build_source_trace(dTrace, oTrace, oDefaultDelay, oLocation):
    # A clock source, such as an oscillator, drives the device and the part on separate traces.
    # Each trace runs from the source to one pin; the traces of one source share its name.
    oTrace.source = READER.get_required_string(dTrace, 'source', oLocation)
    if 'device_pin' in dTrace:
        oTrace.device_pin = READER.get_required_string(dTrace, 'device_pin', oLocation)
        oTrace.source_to_device = build_trace_delay(dTrace, oTrace.name, 'source_to_device', oDefaultDelay, oLocation)
    if 'part_pin' in dTrace:
        oTrace.part_pin = READER.get_required_string(dTrace, 'part_pin', oLocation)
        oTrace.source_to_part = build_trace_delay(dTrace, oTrace.name, 'source_to_part', oDefaultDelay, oLocation)
    if oTrace.source_to_device is None and oTrace.source_to_part is None:
        READER.raise_error(7, oLocation.filename, f'trace {oTrace.name} has neither source_to_device nor source_to_part')
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
    return read_delays(dDelays, False, f'trace {sTraceName} key "{sDirection}"', oDelayLocation)


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
