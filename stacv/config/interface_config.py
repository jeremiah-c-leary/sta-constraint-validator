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
    for dInterface in dConfig['interface']:
        oInterface = config.Interface()
        oInterface.name = dInterface['name']
        for dPort in dInterface['port']:
            oPort = config.Port()
            oPort.name = dPort['name']
            oPort.methodology = dPort['methodology']
            for sTimingReportFilename in dPort['timing_reports']:
                oPort.add_timing_report(os.path.expandvars(sTimingReportFilename))
            oInterface.add_port(oPort)
        oConfig.add_interface(oInterface)
    return oConfig
