'''
Provides functions to read configuration files.
'''

import os
import tomllib

from stacv.config import config
from stacv.config import interface_config_error
from stacv.config import value_type


def read_interface_config(sConfigFile):
    dConfig = read_toml_file(sConfigFile)
    return create_interface_config(dConfig, sConfigFile)


def read_toml_file(sConfigFile):
    with open(sConfigFile, 'rb') as oFile:
        try:
            dConfig = tomllib.load(oFile)
        except tomllib.TOMLDecodeError as oError:
            raise interface_config_error.InterfaceConfigError('interface_config_001', sConfigFile, f'is not valid TOML: {oError}') from oError
    return dConfig


def create_interface_config(dConfig, sConfigFile):
    oConfig = config.InterfaceConfig()
    oLocation = config.ConfigLocation(sConfigFile)
    oConfig.description = get_required_string(dConfig, 'description', oLocation)
    oConfig.interfaces = create_interfaces(dConfig, oLocation)
    return oConfig


def create_interfaces(dConfig, oLocation):
    lInterfaces = []
    for iInterface, dInterface in enumerate(get_required_array_of_tables(dConfig, 'interface', oLocation), start=1):
        oInterface = config.Interface()
        oLocation.set_interface_number(iInterface)
        oInterface.name = get_required_string(dInterface, 'name', oLocation)
        oLocation.set_interface_name(oInterface.name)
        oInterface.ports = create_ports(dInterface, oLocation)
        lInterfaces.append(oInterface)
    return lInterfaces


def create_ports(dInterface, oLocation):
    lPorts = []
    for iPort, dPort in enumerate(get_required_array_of_tables(dInterface, 'port', oLocation), start=1):
        oPort = config.Port()
        oLocation.set_port_number(iPort)
        oPort.name = get_required_string(dPort, 'name', oLocation)
        oLocation.set_port_name(oPort.name)
        oPort.methodology = get_required_string(dPort, 'methodology', oLocation)
        oPort.timing_reports = format_timing_report_names(dPort, oLocation)
        lPorts.append(oPort)
    return lPorts


def format_timing_report_names(dPort, oLocation):
    lTimingReports = []
    for sTimingReportFilename in get_required_list_of_strings(dPort, 'timing_reports', oLocation):
        lTimingReports.append(os.path.expandvars(sTimingReportFilename))
    return lTimingReports


def get_required_key_value(dDict, sKey, oLocation):
    if sKey not in dDict:
        raise interface_config_error.InterfaceConfigError('interface_config_002', oLocation.filename, f'missing required key "{sKey}"{oLocation.location}')
    return dDict[sKey]


def get_required_list_of_strings(dDict, sKey, oLocation):
    value = get_required_key_value(dDict, sKey, oLocation)
    check_schema(value_type.LIST_OF_STRINGS, value, sKey, oLocation)
    return value


def get_required_string(dDict, sKey, oLocation):
    value = get_required_key_value(dDict, sKey, oLocation)
    check_schema(value_type.STRING, value, sKey, oLocation)
    return value


def get_required_array_of_tables(dDict, sKey, oLocation):
    value = get_required_key_value(dDict, sKey, oLocation)
    check_schema(value_type.ARRAY_OF_TABLES, value, sKey, oLocation)
    return value


def check_schema(oExpectedType, value, sKey, oLocation):
    if not oExpectedType.is_valid(value):
        raise interface_config_error.InterfaceConfigError('interface_config_003', oLocation.filename, f'key "{sKey}"{oLocation.location} must be {oExpectedType.description}')
