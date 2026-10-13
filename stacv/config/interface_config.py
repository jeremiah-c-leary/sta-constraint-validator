'''
Provides functions to read configuration files.
'''

import os
import tomllib

from stacv.config import config


def read_interface_config(sConfigFile):
    dConfig = read_toml_file(sConfigFile)
    return convert_dict_to_config_object(dConfig)


def read_toml_file(sConfigFile):
    with open(sConfigFile, 'rb') as f:
        dConfig = tomllib.load(f)
    return dConfig


def convert_dict_to_config_object(dConfig):
    oConfig = config.Config()
    oConfig.description = dConfig['description']    
    oConfig.interfaces = extract_interfaces_from_configuration(dConfig)
    return oConfig


def extract_interfaces_from_configuration(dConfig):
    lInterfaces = []
    for dInterface in dConfig['interface']:
        oInterface = config.Interface()
        oInterface.name = dInterface['name']
        oInterface.ports = extract_ports_from_interface(dInterface)
        lInterfaces.append(oInterface)
    return lInterfaces


def extract_ports_from_interface(dInterface):
    lPorts = []
    for dPort in dInterface['port']:
        oPort = config.Port()
        oPort.name = dPort['name']
        oPort.methodology = dPort['methodology']
        oPort.timing_reports = extract_timing_reports_from_port(dPort)
        lPorts.append(oPort)
    return lPorts


def extract_timing_reports_from_port(dPort):
    lTimingReports = []
    for sTimingReportFilename in dPort['timing_reports']:
        lTimingReports.append(os.path.expandvars(sTimingReportFilename))
    return lTimingReports
