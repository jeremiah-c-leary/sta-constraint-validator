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
    for iInterface, dInterface in enumerate(get_required_key_value(dConfig, 'interface', sConfigFile), start=1):
        oInterface = config.Interface()
        oInterface.name = get_required_key_value(dInterface, 'name', sConfigFile, None, iInterface)
        oInterface.ports = create_ports(dInterface, sConfigFile, oInterface.name)
        lInterfaces.append(oInterface)
    return lInterfaces


def create_ports(dInterface, sConfigFile, sInterface):
    lPorts = []
    for iPort, dPort in enumerate(dInterface['port'], start=1):
        oPort = config.Port()
        oPort.name = get_required_key_value(dPort, 'name', sConfigFile, sInterface, None, None, iPort)
        oPort.methodology = get_required_key_value(dPort, 'methodology', sConfigFile, sInterface, None, oPort.name) 
        oPort.timing_reports = format_timing_report_names(dPort)
        lPorts.append(oPort)
    return lPorts


def format_timing_report_names(dPort):
    lTimingReports = []
    for sTimingReportFilename in dPort['timing_reports']:
        lTimingReports.append(os.path.expandvars(sTimingReportFilename))
    return lTimingReports


def get_required_key_value(dDict, sKey, sConfigFile, sInterface=None, iInterfaceNumber=None, sPort=None, iPortNumber=None):
    if sKey not in dDict:
        sLocation = create_location_string(sInterface, iInterfaceNumber, sPort, iPortNumber)
        raise interface_config_error.InterfaceConfigError('interface_config_002', sConfigFile, f'missing required key "{sKey}"{sLocation}')
    return dDict[sKey]
    

def create_location_string(sInterface, iInterfaceNumber, sPort, iPortNumber):
    sLocation = add_interface(sInterface, iInterfaceNumber)
    return add_port(sLocation, sPort, iPortNumber)


def add_interface(sInterface, iInterfaceNumber):
    if sInterface is None:
        if iInterfaceNumber is None:
            return ''
        return f' in interface number {iInterfaceNumber}'
    return f' in interface {sInterface}' 


def add_port(sLocation, sPort, iPortNumber):
    if sPort is None:
        if iPortNumber is None:
            return sLocation
        return sLocation + f' port number {iPortNumber}'
    return sLocation + f' port {sPort}'
