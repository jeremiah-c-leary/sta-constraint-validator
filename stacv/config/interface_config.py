'''
Provides functions to read configuration files.
'''

import os
import tomllib

from stacv.config import config


def read_interface_config(sConfigFile):
    dConfig = read_toml_file(sConfigFile)
    return create_config_object(dConfig)


def read_toml_file(sConfigFile):
    with open(sConfigFile, 'rb') as oFile:
        dConfig = tomllib.load(oFile)
    return dConfig


def create_config_object(dConfig):
    oConfig = config.InterfaceConfig()
    oConfig.description = dConfig['description']
    oConfig.interfaces = create_interfaces(dConfig)
    return oConfig


def create_interfaces(dConfig):
    lInterfaces = []
    for dInterface in dConfig['interface']:
        oInterface = config.Interface()
        oInterface.name = dInterface['name']
        oInterface.ports = create_ports(dInterface)
        lInterfaces.append(oInterface)
    return lInterfaces


def create_ports(dInterface):
    lPorts = []
    for dPort in dInterface['port']:
        oPort = config.Port()
        oPort.name = dPort['name']
        oPort.methodology = dPort['methodology']
        oPort.timing_reports = create_timing_reports(dPort)
        lPorts.append(oPort)
    return lPorts


def create_timing_reports(dPort):
    lTimingReports = []
    for sTimingReportFilename in dPort['timing_reports']:
        lTimingReports.append(os.path.expandvars(sTimingReportFilename))
    return lTimingReports
