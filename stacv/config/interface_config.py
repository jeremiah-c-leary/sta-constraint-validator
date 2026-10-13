'''
Provides functions to read configuration files.
'''

import os
import tomllib

from stacv.config import config
from stacv.config import interface_config_error


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
    oConfig.description = get_required_key_value(dConfig, 'description', sConfigFile)
    oConfig.interfaces = create_interfaces(dConfig, sConfigFile)
    return oConfig


def create_interfaces(dConfig, sConfigFile):
    lInterfaces = []
    for dInterface in get_required_key_value(dConfig, 'interface', sConfigFile):
        oInterface = config.Interface()
        oInterface.name = dInterface['name']
        oInterface.ports = create_ports(dInterface, sConfigFile, oInterface.name)
        lInterfaces.append(oInterface)
    return lInterfaces


def create_ports(dInterface, sConfigFile, sInterface):
    lPorts = []
    for dPort in dInterface['port']:
        oPort = config.Port()
        oPort.name = dPort['name']
        oPort.methodology = get_required_key_value(dPort, 'methodology', sConfigFile, sInterface, oPort.name) 
        oPort.timing_reports = format_timing_report_names(dPort)
        lPorts.append(oPort)
    return lPorts


def format_timing_report_names(dPort):
    lTimingReports = []
    for sTimingReportFilename in dPort['timing_reports']:
        lTimingReports.append(os.path.expandvars(sTimingReportFilename))
    return lTimingReports


def get_required_key_value(dDict, sKey, sConfigFile, sInterface=None, sPort=None):
    if sKey not in dDict:
        sLocation = create_location_string(sInterface, sPort)
        raise interface_config_error.InterfaceConfigError('interface_config_002', sConfigFile, f'missing required key "{sKey}"{sLocation}')
    return dDict[sKey]


def create_location_string(sInterface, sPort):
    sLocation = add_interface(sInterface)
    return add_port(sLocation, sPort)


def add_interface(sInterface):
    if sInterface is None:
        return ''
    return f' in interface {sInterface}' 


def add_port(sLocation, sPort):
    if sPort is None:
        return sLocation
    return sLocation + f' port {sPort}'
