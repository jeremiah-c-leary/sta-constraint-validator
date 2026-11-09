'''
Reads an RMII configuration file: the names in the design of an RMII interface, with the device as the MAC.

RMII fixes everything else: REF_CLK runs at 50 MHz, and every signal changes and is sampled on its rising edge, so
the file gives only the clock, the port and register of each signal, and the files it is linked to.  stacv expands it
into an interface file whenever a command reads it.
'''

import os
import tomllib

from stacv.config import config_reader
from stacv.rmii import rmii_config_error
from stacv.spi import spi_config_location
from stacv.standards import standards

READER = config_reader.ConfigReader('rmii_config', rmii_config_error.RmiiConfigError)
CONFIGURATION = 'rmii'
PLACEHOLDER = 'FROM_DESIGN'
STANDARD = 'RMII'
TOP_LEVEL_KEYS = ['interface', 'name', 'role', 'part', 'traces', 'timing_reports_dir', 'ref_clk', 'txd', 'tx_en', 'tx_er', 'rxd', 'crs_dv', 'rx_er']
REF_CLK_KEYS = ['name', 'port']
SIGNAL_KEYS = ['port', 'register']
# Each signal's table, the signal it carries, and whether an interface may leave it out.
SIGNALS = [('txd', 'TXD', False), ('tx_en', 'TX_EN', False), ('tx_er', 'TX_ER', True), ('rxd', 'RXD', False), ('crs_dv', 'CRS_DV', False), ('rx_er', 'RX_ER', True)]
# REF_CLK is 50 MHz in RMII.
REF_CLK_PERIOD = 20.0
# The interface of a part template, used until the part file can be read.
DEFAULT_PART_INTERFACE = 'RMII'


class RmiiConfig():

    def __init__(self):
        self.filename = None
        self.location = None
        self.name = None
        self.role = None
        self.part_as_written = None
        self.traces_as_written = None
        self.timing_reports_dir = None
        self.ref_clk = None
        # The signals the interface has, in the order of SIGNALS; an optional signal left out is not in it.
        self.signals = []


class RefClk():

    def __init__(self):
        self.name = None
        self.port = None


class Signal():

    def __init__(self):
        self.signal = None
        self.port = None
        self.register = None


def read_rmii_config(sFilename):
    # The file has already been read as TOML by the interface reader, so it exists and is valid.
    with open(sFilename) as oFile:
        sText = oFile.read()
    oLocation = spi_config_location.SpiConfigLocation(sFilename, sText.split('\n'))
    return create_rmii_config(tomllib.loads(sText), oLocation)


def create_rmii_config(dConfig, oLocation):
    oLocation.set_table(None)
    READER.check_keys(dConfig, TOP_LEVEL_KEYS, oLocation)
    oConfig = RmiiConfig()
    oConfig.filename = oLocation.filename
    oConfig.location = oLocation
    oConfig.name = read_string(dConfig, None, 'name', oLocation)
    oConfig.role = read_role(dConfig, oLocation)
    oConfig.part_as_written = read_string(dConfig, None, 'part', oLocation)
    oConfig.traces_as_written = read_string(dConfig, None, 'traces', oLocation)
    oConfig.timing_reports_dir = read_string(dConfig, None, 'timing_reports_dir', oLocation)
    oConfig.ref_clk = read_ref_clk(dConfig, oLocation)
    for sTable, sSignal, bOptional in SIGNALS:
        if bOptional and sTable not in dConfig:
            continue
        oConfig.signals.append(read_signal(dConfig, sTable, sSignal, oLocation))
    return oConfig


def read_string(dTable, sTable, sKey, oLocation):
    oLocation.set_key(sTable, sKey)
    sValue = READER.get_required_string(dTable, sKey, oLocation)
    if is_placeholder(sValue):
        READER.raise_error(6, oLocation.filename, f'key "{sKey}"{oLocation.location} is {sValue}; replace it with the name in your design')
    return sValue


def is_placeholder(sValue):
    # A template names each placeholder after the key it fills, such as FROM_DESIGN_TXD_PORT, so each can be found.
    return sValue.startswith(PLACEHOLDER)


def read_role(dConfig, oLocation):
    sRole = read_string(dConfig, None, 'role', oLocation)
    if sRole != standards.MAC:
        READER.raise_error(8, oLocation.filename, f'key "role"{oLocation.location} must be "{standards.MAC}"; a {standards.PHY} is not supported yet')
    return sRole


def read_table(dConfig, sTable, lKeys, oLocation):
    oLocation.set_key(None, sTable)
    dTable = READER.get_required_table(dConfig, sTable, oLocation)
    oLocation.set_table(sTable)
    READER.check_keys(dTable, lKeys, oLocation)
    return dTable


def read_ref_clk(dConfig, oLocation):
    dTable = read_table(dConfig, 'ref_clk', REF_CLK_KEYS, oLocation)
    oRefClk = RefClk()
    oRefClk.name = read_string(dTable, 'ref_clk', 'name', oLocation)
    oRefClk.port = read_string(dTable, 'ref_clk', 'port', oLocation)
    return oRefClk


def read_signal(dConfig, sTable, sSignal, oLocation):
    dTable = read_table(dConfig, sTable, SIGNAL_KEYS, oLocation)
    oSignal = Signal()
    oSignal.signal = sSignal
    oSignal.port = read_string(dTable, sTable, 'port', oLocation)
    oSignal.register = read_string(dTable, sTable, 'register', oLocation)
    return oSignal


def find_part_interface(oConfig):
    # The part's RMII interface is the one that follows RMII as the PHY.  The part file is read only once it exists
    # and is valid; until then the commands that need it stop on it.
    dPart = read_part_file(resolve_part_path(oConfig))
    if dPart is None:
        return DEFAULT_PART_INTERFACE
    lNames = find_matching_part_interfaces(dPart)
    if len(lNames) == 1:
        return lNames[0]
    oConfig.location.set_key(None, 'part')
    sInterfaces = f'[[interface]] with if_standard "{STANDARD}" and if_role "{standards.PHY}"'
    if len(lNames) == 0:
        READER.raise_error(12, oConfig.filename, f'key "part"{oConfig.location.location} names {oConfig.part_as_written}, which has no {sInterfaces}')
    READER.raise_error(13, oConfig.filename, f'key "part"{oConfig.location.location} names {oConfig.part_as_written}, which has more than one {sInterfaces}: {", ".join(lNames)}')


def resolve_part_path(oConfig):
    sPath = os.path.expandvars(oConfig.part_as_written)
    if os.path.isabs(sPath):
        return sPath
    return os.path.join(os.path.dirname(oConfig.filename), sPath)


def read_part_file(sFilename):
    if not os.path.isfile(sFilename):
        return None
    try:
        with open(sFilename, 'rb') as oFile:
            return tomllib.load(oFile)
    except tomllib.TOMLDecodeError:
        return None


def find_matching_part_interfaces(dPart):
    lNames = []
    lInterfaces = dPart.get('interface')
    if not isinstance(lInterfaces, list):
        return lNames
    for dInterface in lInterfaces:
        if isinstance(dInterface, dict) and dInterface.get('if_standard') == STANDARD and dInterface.get('if_role') == standards.PHY:
            lNames.append(dInterface.get('name'))
    return lNames


def build_clock_lines(oConfig):
    # The clock, for the constraints file's references.
    return [f'REF_CLK  {oConfig.ref_clk.name} 20 ns']
