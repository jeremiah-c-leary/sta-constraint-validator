'''
Provides functions to read configuration files.
'''

import math
import os
import pathlib
import re

from stacv.config import config_reader
from stacv.config import value_type
from stacv.interface import interface
from stacv.interface import port
from stacv.interface import interface_location
from stacv.interface import interface_config_error
from stacv.methodology import methodology
from stacv.methodology import methodology_factory
from stacv.output import number_format
from stacv.rules import edge_times
from stacv.rules import requirements
from stacv.spi import spi_config
from stacv.spi import spi_interface
from stacv.interface import clock
from stacv.interface import clock_pin
from stacv.interface import clock_generator
from stacv.visualize import edges

IDLE_LEVELS = ['low', 'high']
SDR_SS_O = 'SDR-SS-O'
# The previous edge of the same type is one clock period, two edges, earlier.
EDGES_PER_PERIOD = 2
READER = config_reader.ConfigReader('interface_config', interface_config_error.InterfaceConfigError)
TOP_LEVEL_KEYS = ['description', 'name', 'part', 'part_interface', 'traces', 'if_standard', 'if_role', 'clock', 'port']
CLOCK_KEYS = ['name', 'period', 'port', 'idle', 'if_signal', 'generator']
GENERATOR_KEYS = ['source', 'master_pin', 'target_pin', 'master_clock']
PORT_KEYS = ['status', 'name', 'methodology', 'if_signal', 'launch_clock', 'capture_clock', 'registers', 'timing_reports']
PORT_CLOCK_KEYS = ['name', 'setup_edge', 'hold_edge']


def read_interface_config(sInterfaceFile):
    oInterface = read_interface_config_for_drawing(sInterfaceFile)
    raise_first_edge_error(oInterface)
    check_forwarded_clocks_have_ports(oInterface, sInterfaceFile)
    resolve_part_and_traces(oInterface, sInterfaceFile)
    return oInterface


def check_forwarded_clocks_have_ports(oInterface, sInterfaceFile):
    # The drawing does not need the port, so only the commands that write or check constraints do.
    oLocation = interface_location.InterfaceLocation(sInterfaceFile)
    for oPort in oInterface.get_analyzed_ports():
        oLocation.set_port_name(oPort.name)
        if oPort.forwarded_clock.port is None:
            sClockRole = methodology.describe_clock_key(oPort.forwarded_clock_key)
            READER.raise_error(21, oLocation.filename, f'key "{oPort.forwarded_clock_key}"{oLocation.location} names clock {oPort.forwarded_clock.name}, which has no key "port"; the {sClockRole} leaves the device on a port')


def resolve_part_and_traces(oInterface, sInterfaceFile):
    # The edges are drawn from the interface file alone, so the part and traces paths are resolved only for the commands that read them.
    oLocation = interface_location.InterfaceLocation(sInterfaceFile)
    oInterface.part = resolve_file(oInterface.part_as_written, 'part', oLocation)
    oInterface.traces = resolve_file(oInterface.traces_as_written, 'traces', oLocation)


def read_interface_config_for_drawing(sInterfaceFile):
    # Errors in the edges can still be drawn, so they are kept on each port instead of raised.
    dConfig = read_file(sInterfaceFile)
    if spi_config.is_interface_configuration(dConfig):
        return create_interface_from_configuration(sInterfaceFile)
    return create_interface_config(dConfig, sInterfaceFile)


def create_interface_from_configuration(sConfigFile):
    # An interface configuration file is expanded into an interface file, so every command reads it the same way.
    oSpiConfig = spi_config.read_spi_config(sConfigFile)
    oInterface = create_interface_config(spi_interface.build_interface_dictionary(oSpiConfig), sConfigFile)
    oInterface.edge_lines = spi_config.build_edge_lines(oSpiConfig)
    return oInterface


def raise_first_edge_error(oInterface):
    for oPort in oInterface.ports:
        for oError in oPort.edge_errors:
            raise oError


def read_file(sInterfaceFile):
    try:
        return READER.read_toml_file(sInterfaceFile)
    except FileNotFoundError:
        raise interface_config_error.InterfaceConfigError('interface_config_007', sInterfaceFile, f'does not exist')


def resolve_timing_reports(oInterface, sInterfaceFile):
    # Only check reads the timing reports, so their environment variables are expanded here and not when the interface is read.
    oLocation = interface_location.InterfaceLocation(sInterfaceFile)
    for oPort in oInterface.ports:
        if is_checked(oPort):
            oLocation.set_port_name(oPort.name)
            oPort.timing_reports = resolve_files(oPort.timing_reports_as_written, 'timing_reports', oLocation)


def is_checked(oPort):
    # A port whose methodology has no rules yet is deferred by check, so its timing reports are not read.
    if oPort.status == port.DEFER:
        return False
    return methodology_factory.create_methodology(oPort.methodology).has_rules()


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
    oInterface.part_as_written = READER.get_required_string(dConfig, 'part', oLocation)
    # The interface of the part this file times; the user names it, so the part's other modes are never used by mistake.
    oInterface.part_interface = READER.get_required_string(dConfig, 'part_interface', oLocation)
    oInterface.traces_as_written = READER.get_required_string(dConfig, 'traces', oLocation)
    oInterface.if_standard = read_optional_string(dConfig, 'if_standard', oLocation)
    oInterface.if_role = read_optional_string(dConfig, 'if_role', oLocation)
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
    oClock.if_signal = read_optional_string(dClock, 'if_signal', oLocation)
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
            check_port_is_not_a_bus(oPort.name, oLocation)
            read_analyzed_port(dPort, oPort, oInterface, oLocation)
            check_port_is_not_defined(lPortKeys, oPort, oLocation)
        else:
            read_deferred_port(dPort, oPort, oLocation)
        lPorts.append(oPort)
    return lPorts


def check_port_is_not_a_bus(sName, oLocation):
    # A bus is written NAME[upper:lower]; any other bracket or a wildcard is not a port name stacv can use.
    if re.fullmatch(r'[A-Za-z_]\w*\[\d+:\d+\]', sName) is not None:
        return
    if '[' in sName or '*' in sName:
        READER.raise_error(22, oLocation.filename, f'port {sName} is not a port name or a bus written NAME[upper:lower]; give each bit its own [[port]], write the bus as NAME[upper:lower], or defer it')


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
    oPort.if_signal = read_optional_string(dPort, 'if_signal', oLocation)


def read_optional_string(dTable, sKey, oLocation):
    if sKey not in dTable:
        return None
    return READER.get_required_string(dTable, sKey, oLocation)


def read_analyzed_port(dPort, oPort, oInterface, oLocation):
    # A deferred port needs only its name and status, so only analyzed ports read the rest.
    oPort.methodology = READER.get_required_string(dPort, 'methodology', oLocation)
    check_methodology_is_supported(oPort.methodology, oLocation)
    oPort.if_signal = read_optional_string(dPort, 'if_signal', oLocation)
    oPort.capture_clock = build_referenced_clock(dPort, 'capture_clock', oPort.name, oInterface, oLocation)
    check_capture_clock_stops_if_needed(oPort, oLocation)
    oPort.launch_clock = build_referenced_clock(dPort, 'launch_clock', oPort.name, oInterface, oLocation)
    set_methodology_roles(oPort)
    oPort.edge_errors = find_edge_errors(oPort, oLocation)
    oPort.timing_reports_as_written = READER.get_required_list_of_strings(dPort, 'timing_reports', oLocation)
    # The registers that drive or capture the port, which every path in its timing reports must start or end at.
    oPort.registers = READER.get_required_list_of_strings(dPort, 'registers', oLocation)


def set_methodology_roles(oPort):
    oMethodology = methodology_factory.create_methodology(oPort.methodology)
    oPort.data_direction = oMethodology.data_direction
    oPort.forwarded_clock_key = oMethodology.forwarded_clock_key
    oPort.clock_origin = oMethodology.clock_origin
    oPort.part_pin_methodology = oMethodology.part_pin_methodology
    oPort.double_data_rate = oMethodology.double_data_rate
    oPort.setup_capture_edges_after_launch = oMethodology.setup_capture_edges_after_launch
    oPort.capture_edge_description = oMethodology.capture_edge_description
    if oPort.forwarded_clock_key == methodology.LAUNCH_CLOCK:
        oPort.forwarded_clock = oPort.launch_clock
    else:
        oPort.forwarded_clock = oPort.capture_clock


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


def find_edge_errors(oPort, oLocation):
    # A double data rate port captures on both edges, so its setup and hold edges can be different types.
    lErrors = []
    if oPort.setup_capture_edges_after_launch is not None:
        return find_double_data_rate_input_edge_errors(oPort, oLocation)
    if oPort.double_data_rate:
        return lErrors
    if not capture_edges_are_the_same_type(oPort.capture_clock):
        lErrors.append(READER.create_error(18, oLocation.filename, f'key "capture_clock"{oLocation.location} has setup_edge {oPort.capture_clock.setup_edge} and hold_edge {oPort.capture_clock.hold_edge}, which are not the same edge type'))
    elif oPort.methodology == SDR_SS_O:
        lErrors.extend(find_sdr_source_synchronous_output_edge_errors(oPort, oLocation))
    return lErrors


def find_sdr_source_synchronous_output_edge_errors(oPort, oLocation):
    # An SDR-SS-O port launches each bit on one edge, and holds it until the capture edge after the one it is set up to.
    lErrors = []
    oLaunchClock = oPort.launch_clock
    if oLaunchClock.setup_edge != oLaunchClock.hold_edge:
        lErrors.append(READER.create_error(19, oLocation.filename, f'key "launch_clock"{oLocation.location} has setup_edge {oLaunchClock.setup_edge} and hold_edge {oLaunchClock.hold_edge}; an SDR-SS-O port launches each bit once, so both must be the same edge (a signal timed to the first and last clock edges is SDR-SS-O-FLC)'))
    oCaptureClock = oPort.capture_clock
    iSetupEdge = edge_times.convert_edge_letter_to_number(oCaptureClock.setup_edge)
    iHoldEdge = edge_times.convert_edge_letter_to_number(oCaptureClock.hold_edge)
    if iHoldEdge != iSetupEdge - EDGES_PER_PERIOD:
        lErrors.append(READER.create_error(20, oLocation.filename, f'key "capture_clock"{oLocation.location} has setup_edge {oCaptureClock.setup_edge} and hold_edge {oCaptureClock.hold_edge}; {describe_expected_capture_hold_edge(iSetupEdge)}'))
    return lErrors


def find_double_data_rate_input_edge_errors(oPort, oLocation):
    # The methodology names the edge that captures each bit, so the edges must give its requirements.
    lErrors = []
    fEdgeTime = oPort.capture_clock.period / EDGES_PER_PERIOD
    fExpectedSetup = oPort.setup_capture_edges_after_launch * fEdgeTime
    fExpectedHold = fExpectedSetup - fEdgeTime
    fSetup = requirements.calculate_configuration_setup_requirement(oPort)
    fHold = requirements.calculate_configuration_hold_requirement(oPort)
    if requirements_match(fSetup, fExpectedSetup) and requirements_match(fHold, fExpectedHold):
        return lErrors
    sRequirements = f'a setup requirement of {format_nanoseconds(fSetup)} and a hold requirement of {format_nanoseconds(fHold)}'
    sExpected = f'{format_nanoseconds(fExpectedSetup)} and {format_nanoseconds(fExpectedHold)}'
    lErrors.append(READER.create_error(23, oLocation.filename, f'the edges{oLocation.location} give {sRequirements}; {oPort.capture_edge_description}, so they must be {sExpected}'))
    return lErrors


def requirements_match(fRequirement, fExpected):
    return math.isclose(fRequirement, fExpected, abs_tol=1e-9)


def format_nanoseconds(fTime):
    return f'{number_format.format_number(fTime)} ns'


def describe_expected_capture_hold_edge(iSetupEdge):
    sRule = 'the hold edge of an SDR-SS-O port is the previous capture edge of the same type'
    if iSetupEdge < EDGES_PER_PERIOD:
        return f'{sRule}, so setup_edge must be C or later'
    return f'{sRule}, {edge_times.convert_edge_number_to_letter(iSetupEdge - EDGES_PER_PERIOD)}'


def capture_edges_are_the_same_type(oCaptureClock):
    iSetupEdge = edge_times.convert_edge_letter_to_number(oCaptureClock.setup_edge)
    iHoldEdge = edge_times.convert_edge_letter_to_number(oCaptureClock.hold_edge)
    return iSetupEdge % 2 == iHoldEdge % 2


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
