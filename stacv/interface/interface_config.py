'''
Provides functions to read configuration files.
'''

import os
import pathlib
import re

from stacv.config import config_reader
from stacv.config import value_type
from stacv.interface import interface
from stacv.interface import port
from stacv.interface import interface_location
from stacv.interface import interface_config_error
from stacv.methodology import methodology_factory
from stacv.interface import clock
from stacv.interface import clock_pin
from stacv.interface import clock_generator
from stacv.visualize import edges

IDLE_LEVELS = ['low', 'high']
READER = config_reader.ConfigReader('interface_config', interface_config_error.InterfaceConfigError)
TOP_LEVEL_KEYS = ['description', 'name', 'part', 'traces', 'clock', 'port']
CLOCK_KEYS = ['name', 'period', 'port', 'idle', 'generator']
GENERATOR_KEYS = ['source', 'master_pin', 'target_pin', 'master_clock']
PORT_KEYS = ['status', 'name', 'methodology', 'launch_clock', 'capture_clock', 'timing_reports']
PORT_CLOCK_KEYS = ['name', 'setup_edge', 'hold_edge']


def read_interface_config(sInterfaceFile):
    dConfig = read_file(sInterfaceFile)
    return create_interface_config(dConfig, sInterfaceFile)


def read_file(sInterfaceFile):
    try:
        return READER.read_toml_file(sInterfaceFile)
    except FileNotFoundError:
        raise interface_config_error.InterfaceConfigError('interface_config_007', sInterfaceFile, f'does not exist')


def resolve_timing_reports(oInterface, sInterfaceFile):
    # Only check reads the timing reports, so their environment variables are expanded here and not when the interface is read.
    oLocation = interface_location.InterfaceLocation(sInterfaceFile)
    for oPort in oInterface.ports:
        oLocation.set_port_name(oPort.name)
        oPort.timing_reports = resolve_files(oPort.timing_reports_as_written, 'timing_reports', oLocation)


def resolve_files(lFilenames, sKey, oLocation):
    lFiles = []
    for sFilename in lFilenames:
        lFiles.append(resolve_file(sFilename, sKey, oLocation))
    return lFiles


def create_interface_config(dConfig, sInterfaceFile):
    oInterface = interface.Interface()
    oLocation = interface_location.InterfaceLocation(sInterfaceFile)
    READER.check_keys(dConfig, TOP_LEVEL_KEYS, oLocation)
    oInterface.description = READER.get_required_string(dConfig, 'description', oLocation)
    oInterface.interface_name = READER.get_required_string(dConfig, 'name', oLocation)
    oInterface.part = get_required_file(dConfig, 'part', oLocation)
    oInterface.traces = get_required_file(dConfig, 'traces', oLocation)
    create_clocks(dConfig, oInterface, oLocation)
    oInterface.ports = create_ports(dConfig, oLocation, oInterface)
    return oInterface


def create_clocks(dConfig, oInterface, oLocation):
    if 'clock' not in dConfig:
        return
    for iClock, dClock in enumerate(READER.get_required_array_of_tables(dConfig, 'clock', oLocation), start=1):
        oClock = build_clock(dClock, iClock, oLocation.filename)
        check_clock_is_not_defined(oInterface, oClock.name, oLocation)
        oInterface.clocks.append(oClock)
    check_master_clocks_are_defined(oInterface, oLocation)


def check_master_clocks_are_defined(oInterface, oLocation):
    for oClock in oInterface.clocks:
        if oClock.generator is not None and oInterface.get_clock_named(oClock.generator.master_clock) is None:
            raise interface_config_error.InterfaceConfigError('interface_config_008', oLocation.filename, f'key "generator" of clock {oClock.name} names clock {oClock.generator.master_clock}, which no [[clock]] table defines')


def check_clock_is_not_defined(oInterface, sName, oLocation):
    if oInterface.get_clock_named(sName) is not None:
        raise interface_config_error.InterfaceConfigError('interface_config_009', oLocation.filename, f'clock {sName} is defined by more than one [[clock]] table')


def build_clock(dClock, iClock, sFilename):
    oLocation = interface_location.InterfaceLocation(sFilename)
    oLocation.set_clock_number(iClock)
    if has_valid_name(dClock):
        oLocation.set_clock_name(dClock['name'])
    READER.check_keys(dClock, CLOCK_KEYS, oLocation)
    oClock = clock.Clock()
    oClock.name = READER.get_required_string(dClock, 'name', oLocation)
    oClock.period = READER.get_required_number(dClock, 'period', oLocation)
    check_period_is_positive(oClock.period, oLocation)
    if 'port' in dClock:
        oClock.port = READER.get_required_string(dClock, 'port', oLocation)
    if 'idle' in dClock:
        oClock.idle = read_idle(dClock, oClock.name, oLocation)
    if 'generator' in dClock:
        oClock.generator = build_clock_generator(READER.get_required_table(dClock, 'generator', oLocation), oClock.name, sFilename)
    return oClock


def check_period_is_positive(fPeriod, oLocation):
    if fPeriod <= 0:
        READER.raise_error(16, oLocation.filename, f'key "period"{oLocation.location} must be greater than 0')


def has_valid_name(dTable):
    # A table is named by its name only once the name is valid; until then it is named by its number.
    return 'name' in dTable and value_type.STRING.is_valid(dTable['name'])


def read_idle(dClock, sClockName, oLocation):
    sIdle = READER.get_required_string(dClock, 'idle', oLocation)
    if sIdle not in IDLE_LEVELS:
        raise interface_config_error.InterfaceConfigError('interface_config_012', oLocation.filename, f'key "idle" of clock {sClockName} must be "{IDLE_LEVELS[0]}" or "{IDLE_LEVELS[1]}"')
    return sIdle


def create_ports(dConfig, oLocation, oInterface):
    lPorts = []
    lPortKeys = []
    for iPort, dPort in enumerate(READER.get_required_array_of_tables(dConfig, 'port', oLocation), start=1):
        oPort = port.Port()
        oLocation.set_port_number(iPort)
        if has_valid_name(dPort):
            oLocation.set_port_name(dPort['name'])
        oPort.status = get_status(dPort, oLocation)
        # A deferred port can be ignored, so only an analyzed port has its keys checked.
        if oPort.status == port.ANALYZE:
            READER.check_keys(dPort, PORT_KEYS, oLocation)
        oPort.name = READER.get_required_string(dPort, 'name', oLocation)
        oLocation.set_port_name(oPort.name)
        if oPort.status == port.ANALYZE:
            read_analyzed_port(dPort, oPort, oInterface, oLocation)
            check_port_is_not_defined(lPortKeys, oPort, oLocation)
        else:
            read_deferred_port(dPort, oPort, oLocation)
        lPorts.append(oPort)
    return lPorts


def check_port_is_not_defined(lPortKeys, oPort, oLocation):
    # A bidirectional port is timed with one methodology for each direction, so a port is identified by both.
    sPortKey = oPort.name + '.' + oPort.methodology
    if sPortKey in lPortKeys:
        READER.raise_error(17, oLocation.filename, f'port {oPort.name} with methodology {oPort.methodology} is defined by more than one [[port]] table')
    lPortKeys.append(sPortKey)


def check_methodology_is_supported(sMethodology, oLocation):
    if not methodology_factory.is_supported(sMethodology):
        raise interface_config_error.InterfaceConfigError('interface_config_011', oLocation.filename, f'key "methodology"{oLocation.location} names {sMethodology}, which stacv does not support; correct it, or defer the port with status = "{port.DEFER}"')


def get_status(dPort, oLocation):
    if 'status' not in dPort:
        return port.ANALYZE
    sStatus = READER.get_required_string(dPort, 'status', oLocation)
    if sStatus not in [port.ANALYZE, port.DEFER]:
        raise interface_config_error.InterfaceConfigError('interface_config_010', oLocation.filename, f'key "status"{oLocation.location} must be "{port.ANALYZE}" or "{port.DEFER}"')
    return sStatus


def read_deferred_port(dPort, oPort, oLocation):
    # A deferred port may name a methodology stacv does not support yet.
    if 'methodology' in dPort:
        oPort.methodology = READER.get_required_string(dPort, 'methodology', oLocation)


def read_analyzed_port(dPort, oPort, oInterface, oLocation):
    # A deferred port needs only its name and status, so only analyzed ports read the rest.
    oPort.methodology = READER.get_required_string(dPort, 'methodology', oLocation)
    check_methodology_is_supported(oPort.methodology, oLocation)
    oPort.capture_clock = build_referenced_clock(dPort, 'capture_clock', oPort.name, oInterface, oLocation)
    check_capture_clock_stops_if_needed(oPort, oLocation)
    oPort.launch_clock = build_referenced_clock(dPort, 'launch_clock', oPort.name, oInterface, oLocation)
    oPort.timing_reports_as_written = READER.get_required_list_of_strings(dPort, 'timing_reports', oLocation)


def get_required_file(dDict, sKey, oLocation):
    sFilename = READER.get_required_string(dDict, sKey, oLocation)
    return resolve_file(sFilename, sKey, oLocation)


def resolve_file(sFilename, sKey, oLocation):
    sFile = resolve_path(sFilename, sKey, oLocation)
    check_if_file_exists(sFile, sKey, oLocation)
    return sFile


def resolve_path(sFilename, sKey, oLocation):
    check_for_unset_environment_variables(sFilename, sKey, oLocation)
    sPath = os.path.expandvars(sFilename)
    return resolve_relative_path(sPath, oLocation)


def build_clock_generator(dGenerator, sClockName, sFilename):
    oLocation = interface_location.InterfaceLocation(sFilename)
    oLocation.set_generator(sClockName)
    READER.check_keys(dGenerator, GENERATOR_KEYS, oLocation)
    oClockGenerator = clock_generator.ClockGenerator()
    oClockGenerator.source = READER.get_required_string(dGenerator, 'source', oLocation)
    oClockGenerator.master_pin = READER.get_required_string(dGenerator, 'master_pin', oLocation)
    oClockGenerator.target_pin = READER.get_required_string(dGenerator, 'target_pin', oLocation)
    oClockGenerator.master_clock = READER.get_required_string(dGenerator, 'master_clock', oLocation)
    return oClockGenerator


def build_referenced_clock(dPort, sKey, sPortName, oInterface, oLocation):
    dClock = READER.get_required_table(dPort, sKey, oLocation)
    oTableLocation = interface_location.InterfaceLocation(oLocation.filename)
    oTableLocation.set_port_table(sKey, sPortName)
    READER.check_keys(dClock, PORT_CLOCK_KEYS, oTableLocation)
    sName = READER.get_required_string(dClock, 'name', oTableLocation)
    oClock = find_defined_clock(oInterface, sName, sKey, oLocation)
    oClockPin = clock_pin.ClockPin()
    oClockPin.name = oClock.name
    oClockPin.period = oClock.period
    oClockPin.port = oClock.port
    oClockPin.generator = oClock.generator
    oClockPin.idle = oClock.idle
    oClockPin.setup_edge = read_edge(dClock, 'setup_edge', sKey, oLocation, oTableLocation)
    oClockPin.hold_edge = read_edge(dClock, 'hold_edge', sKey, oLocation, oTableLocation)
    return oClockPin


def read_edge(dClock, sEdge, sKey, oPortLocation, oTableLocation):
    # Edges are written by role: launch edges are numbers and capture edges are letters.
    edge = READER.get_required_key_value(dClock, sEdge, oTableLocation)
    if sKey == 'launch_clock':
        check_launch_edge(edge, sEdge, sKey, oPortLocation)
    else:
        check_capture_edge(edge, sEdge, sKey, oPortLocation)
    return edge


def check_launch_edge(edge, sEdge, sKey, oLocation):
    if not is_launch_edge(edge):
        READER.raise_error(14, oLocation.filename, f'key "{sKey}"{oLocation.location} has {sEdge} {format_edge(edge)}; launch edges are numbers: 0, 1, 2, ...')


def check_capture_edge(edge, sEdge, sKey, oLocation):
    if not is_capture_edge(edge):
        READER.raise_error(15, oLocation.filename, f'key "{sKey}"{oLocation.location} has {sEdge} {format_edge(edge)}; capture edges are letters: A, B, C, ...')


def is_launch_edge(edge):
    # A TOML true or false is a bool, which Python also counts as an int.
    if isinstance(edge, bool) or not isinstance(edge, int):
        return False
    return edge >= 0


def is_capture_edge(edge):
    if not isinstance(edge, str):
        return False
    return re.fullmatch('[A-Z]+', edge) is not None


def format_edge(edge):
    # Shows the edge as it is written in the file, with quotes around text.
    if isinstance(edge, str):
        return f'"{edge}"'
    return str(edge)


def check_capture_clock_stops_if_needed(oPort, oLocation):
    # The first and last edges of a clock only exist if the clock stops, and the drawing needs its idle level.
    oMethodology = methodology_factory.create_methodology(oPort.methodology)
    if oMethodology.edge_diagram_type != edges.FIRST_LAST_CLOCK:
        return
    if oPort.capture_clock.idle is None:
        raise interface_config_error.InterfaceConfigError('interface_config_013', oLocation.filename, f'key "capture_clock"{oLocation.location} names clock {oPort.capture_clock.name}, which has no key "idle"; {oPort.methodology} is timed to the first and last edges of a clock that stops')


def find_defined_clock(oInterface, sName, sKey, oLocation):
    oClock = oInterface.get_clock_named(sName)
    if oClock is None:
        raise interface_config_error.InterfaceConfigError('interface_config_008', oLocation.filename, f'key "{sKey}"{oLocation.location} names clock {sName}, which no [[clock]] table defines')
    return oClock


def check_for_unset_environment_variables(sString, sKey, oLocation):
    lUnsetVars = extract_unset_environment_variables(sString)
    if unset_variables_exist(lUnsetVars):
        raise interface_config_error.InterfaceConfigError('interface_config_005', oLocation.filename, f'key "{sKey}"{oLocation.location} uses environment variables that are not set: {", ".join(lUnsetVars)}')


def resolve_relative_path(sFilename, oLocation):
    sExpandedPath = sFilename
    if not pathlib.Path(sExpandedPath).is_absolute():
        oParentPath = os.path.dirname(oLocation.filename)
        sExpandedPath = os.path.join(oParentPath, sFilename)
    return os.path.normpath(sExpandedPath)


def extract_unset_environment_variables(sString):
    lUnsetVars = []
    for sVar in re.findall(r'\${?(\w+)}?', sString):
        if sVar not in os.environ:
            lUnsetVars.append(sVar)
    return lUnsetVars


def unset_variables_exist(lList):
    return len(lList) > 0


def check_if_file_exists(sFilename, sKey, oLocation):
    if not pathlib.Path(sFilename).is_file():
        raise interface_config_error.InterfaceConfigError('interface_config_006', oLocation.filename, f'key "{sKey}"{oLocation.location} names a file that does not exist: {sFilename}')
