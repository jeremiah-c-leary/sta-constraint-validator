'''
Provides functions to read configuration files.
'''

import os
import pathlib
import re
import tomllib

from stacv.interface import interface
from stacv.interface import port
from stacv.interface import interface_location
from stacv.interface import interface_config_error
from stacv.interface import value_type
from stacv.interface import clock
from stacv.interface import clock_pin
from stacv.interface import clock_generator


def read_interface_config(sInterfaceFile):
    dConfig = read_file(sInterfaceFile)
    return create_interface_config(dConfig, sInterfaceFile)


def read_file(sInterfaceFile):
    try:
        return read_toml_file(sInterfaceFile)
    except FileNotFoundError:
        raise interface_config_error.InterfaceConfigError('interface_config_006', sInterfaceFile, f'does not exist')


def read_toml_file(sInterfaceFile):
    with open(sInterfaceFile, 'rb') as oFile:
        try:
            return tomllib.load(oFile)
        except tomllib.TOMLDecodeError as oError:
            raise interface_config_error.InterfaceConfigError('interface_config_001', sInterfaceFile, f'is not valid TOML: {oError}') from oError


def check_timing_reports_exist(oInterface, sInterfaceFile):
    oLocation = interface_location.InterfaceLocation(sInterfaceFile)
    for oPort in oInterface.ports:
        oLocation.set_port_name(oPort.name)
        for sTimingReport in oPort.timing_reports:
            check_if_file_exists(sTimingReport, 'timing_reports', oLocation)


def create_interface_config(dConfig, sInterfaceFile):
    oInterface = interface.Interface()
    oLocation = interface_location.InterfaceLocation(sInterfaceFile)
    oInterface.description = get_required_string(dConfig, 'description', oLocation)
    oInterface.interface_name = get_required_string(dConfig, 'name', oLocation)
    oInterface.part = get_required_file(dConfig, 'part', oLocation)
    oInterface.traces = get_required_file(dConfig, 'traces', oLocation)
    oInterface.clocks = create_clocks(dConfig, oLocation)
    oInterface.ports = create_ports(dConfig, oLocation, oInterface.clocks)
    return oInterface


def create_clocks(dConfig, oLocation):
    lClocks = []
    if 'clock' not in dConfig:
        return lClocks
    for dClock in dConfig['clock']:
        oClock = build_clock(dClock)
        check_clock_is_not_defined(lClocks, oClock.name, oLocation)
        lClocks.append(oClock)
    return lClocks


def check_clock_is_not_defined(lClocks, sName, oLocation):
    if find_clock(lClocks, sName) is not None:
        raise interface_config_error.InterfaceConfigError('interface_config_008', oLocation.filename, f'clock {sName} is defined by more than one [[clock]] table')


def build_clock(dClock):
    oClock = clock.Clock()
    oClock.name = dClock['name']
    oClock.period = dClock['period']
    if 'port' in dClock:
        oClock.port = dClock['port']
    if 'generator' in dClock:
        oClock.generator = build_clock_generator(dClock['generator'])
    return oClock


def find_clock(lClocks, sName):
    for oClock in lClocks:
        if oClock.name == sName:
            return oClock
    return None


def create_ports(dConfig, oLocation, lClocks):
    lPorts = []
    for iPort, dPort in enumerate(get_required_array_of_tables(dConfig, 'port', oLocation), start=1):
        oPort = port.Port()
        oLocation.set_port_number(iPort)
        oPort.name = get_required_string(dPort, 'name', oLocation)
        oLocation.set_port_name(oPort.name)
        oPort.methodology = get_required_string(dPort, 'methodology', oLocation)
        oPort.capture_clock = build_capture_clock(dPort['capture_clock'], lClocks, oLocation)
        oPort.launch_clock = build_launch_clock(dPort['launch_clock'], lClocks, oLocation)
        oPort.timing_reports = get_required_list_of_paths(dPort, 'timing_reports', oLocation)
        lPorts.append(oPort)
    return lPorts


def get_required_array_of_tables(dDict, sKey, oLocation):
    value = get_required_key_value(dDict, sKey, oLocation)
    check_schema(value_type.ARRAY_OF_TABLES, value, sKey, oLocation)
    return value


def get_required_key_value(dDict, sKey, oLocation):
    if sKey not in dDict:
        raise interface_config_error.InterfaceConfigError('interface_config_002', oLocation.filename, f'missing required key "{sKey}"{oLocation.location}')
    return dDict[sKey]


def get_required_list_of_paths(dDict, sKey, oLocation):
    lPaths = []
    for sFilename in get_required_list_of_strings(dDict, sKey, oLocation):
        sPath = resolve_path(sFilename, sKey, oLocation)
        lPaths.append(sPath)
    return lPaths


def get_required_file(dDict, sKey, oLocation):
    sFilename = get_required_string(dDict, sKey, oLocation)
    return resolve_file(sFilename, sKey, oLocation)


def resolve_file(sFilename, sKey, oLocation):
    sFile = resolve_path(sFilename, sKey, oLocation)
    check_if_file_exists(sFile, sKey, oLocation)
    return sFile


def resolve_path(sFilename, sKey, oLocation):
    check_for_unset_environment_variables(sFilename, sKey, oLocation)
    sPath = os.path.expandvars(sFilename)
    return resolve_relative_path(sPath, oLocation)


def get_required_list_of_strings(dDict, sKey, oLocation):
    value = get_required_key_value(dDict, sKey, oLocation)
    check_schema(value_type.LIST_OF_STRINGS, value, sKey, oLocation)
    return value


def get_required_string(dDict, sKey, oLocation):
    value = get_required_key_value(dDict, sKey, oLocation)
    check_schema(value_type.STRING, value, sKey, oLocation)
    return value


def check_schema(oExpectedType, value, sKey, oLocation):
    if not oExpectedType.is_valid(value):
        raise interface_config_error.InterfaceConfigError('interface_config_003', oLocation.filename, f'key "{sKey}"{oLocation.location} must be {oExpectedType.description}')


def build_capture_clock(dClock, lClocks, oLocation):
    if not is_inline_clock(dClock):
        return build_referenced_clock(dClock, lClocks, 'capture_clock', oLocation)
    oClockPin = clock_pin.ClockPin()
    oClockPin.port = dClock['port']
    oClockPin.name = dClock['name']
    oClockPin.period = dClock['period']
    if 'generator' in dClock:
        oClockPin.generator = build_clock_generator(dClock['generator'])
    oClockPin.setup_edge = dClock['setup_edge']
    oClockPin.hold_edge = dClock['hold_edge']
    return oClockPin


def build_clock_generator(dGenerator):
    oClockGenerator = clock_generator.ClockGenerator()
    oClockGenerator.source = dGenerator['source']
    oClockGenerator.master_pin = dGenerator['master_pin']
    oClockGenerator.target_pin = dGenerator['target_pin']
    if 'master_clock' in dGenerator:
        oClockGenerator.master_clock = dGenerator['master_clock']
    return oClockGenerator


def build_launch_clock(dClock, lClocks, oLocation):
    if not is_inline_clock(dClock):
        return build_referenced_clock(dClock, lClocks, 'launch_clock', oLocation)
    oClockPin = clock_pin.ClockPin()
    oClockPin.name = dClock['name']
    oClockPin.period = dClock['period']
    oClockPin.setup_edge = dClock['setup_edge']
    oClockPin.hold_edge = dClock['hold_edge']
    return oClockPin


def is_inline_clock(dClock):
    # The clock is described in the port, instead of referring to a [[clock]] table.
    return 'period' in dClock


def build_referenced_clock(dClock, lClocks, sKey, oLocation):
    oClock = find_defined_clock(lClocks, dClock['name'], sKey, oLocation)
    oClockPin = clock_pin.ClockPin()
    oClockPin.name = oClock.name
    oClockPin.period = oClock.period
    oClockPin.port = oClock.port
    oClockPin.generator = oClock.generator
    oClockPin.setup_edge = dClock['setup_edge']
    oClockPin.hold_edge = dClock['hold_edge']
    return oClockPin


def find_defined_clock(lClocks, sName, sKey, oLocation):
    oClock = find_clock(lClocks, sName)
    if oClock is None:
        raise interface_config_error.InterfaceConfigError('interface_config_007', oLocation.filename, f'key "{sKey}"{oLocation.location} names clock {sName}, which no [[clock]] table defines')
    return oClock


def check_for_unset_environment_variables(sString, sKey, oLocation):
    lUnsetVars = extract_unset_environment_variables(sString)
    if unset_variables_exist(lUnsetVars):
        raise interface_config_error.InterfaceConfigError('interface_config_004', oLocation.filename, f'key "{sKey}"{oLocation.location} uses environment variables that are not set: {", ".join(lUnsetVars)}')


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
        raise interface_config_error.InterfaceConfigError('interface_config_005', oLocation.filename, f'key "{sKey}"{oLocation.location} names a file that does not exist: {sFilename}')
