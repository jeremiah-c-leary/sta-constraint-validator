'''
Provides functions to read configuration files.
'''

import os
import pathlib
import re
import tomllib

from stacv.interface import config
from stacv.interface import interface_config_error
from stacv.interface import value_type
from stacv.interface import clock_pin


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


def create_interface_config(dConfig, sInterfaceFile):
    oInterface = config.Interface()
    oLocation = config.ConfigLocation(sInterfaceFile)
    oInterface.description = get_required_string(dConfig, 'description', oLocation)
    oInterface.interface_name = get_required_string(dConfig, 'interface', oLocation)
    oInterface.part = get_required_file(dConfig, 'part', oLocation)
    oInterface.traces = get_required_file(dConfig, 'traces', oLocation)
    oInterface.ports = create_ports(dConfig, oLocation)
    return oInterface


def create_ports(dConfig, oLocation):
    lPorts = []
    for iPort, dPort in enumerate(get_required_array_of_tables(dConfig, 'port', oLocation), start=1):
        oPort = config.Port()
        oLocation.set_port_number(iPort)
        oPort.name = get_required_string(dPort, 'name', oLocation)
        oLocation.set_port_name(oPort.name)
        oPort.methodology = get_required_string(dPort, 'methodology', oLocation)
        oPort.capture_clock = build_capture_clock(dPort['capture_clock'])
        oPort.launch_clock = build_launch_clock(dPort['launch_clock'])
        oPort.timing_reports = get_required_list_of_files(dPort, 'timing_reports', oLocation)
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


def get_required_list_of_files(dDict, sKey, oLocation):
    lFiles = []
    for sFilename in get_required_list_of_strings(dDict, sKey, oLocation):
        sFile = resolve_file(sFilename, sKey, oLocation)
        lFiles.append(sFile)
    return lFiles


def get_required_file(dDict, sKey, oLocation):
    sFilename = get_required_string(dDict, sKey, oLocation)
    return resolve_file(sFilename, sKey, oLocation)


def resolve_file(sFilename, sKey, oLocation):
    check_for_unset_environment_variables(sFilename, sKey, oLocation)
    sFile = os.path.expandvars(sFilename)
    sFile = resolve_relative_path(sFile, oLocation)
    check_if_file_exists(sFile, sKey, oLocation)
    return sFile


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


def build_capture_clock(dClock):
    oClockPin = clock_pin.ClockPin()
    oClockPin.port = dClock['port']
    oClockPin.name = dClock['name']
    oClockPin.period = dClock['period']
    oClockPin.setup_edge = dClock['setup_edge']
    oClockPin.hold_edge = dClock['hold_edge']
    return oClockPin


def build_launch_clock(dClock):
    oClockPin = clock_pin.ClockPin()
    oClockPin.name = dClock['name']
    oClockPin.period = dClock['period']
    oClockPin.setup_edge = dClock['setup_edge']
    oClockPin.hold_edge = dClock['hold_edge']
    return oClockPin


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
