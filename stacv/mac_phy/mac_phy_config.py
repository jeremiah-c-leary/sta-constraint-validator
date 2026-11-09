'''
Reads an RMII or MII configuration file: the names in the design of a MAC to PHY interface, with the device as the
MAC.

The standard fixes everything else: the clocks' periods, and the rising edges every signal changes and is sampled on,
so the file gives only the clocks' names and ports, the port and register of each signal, and the files it is linked
to.  stacv expands it into an interface file whenever a command reads it.
'''

import os
import re
import tomllib

from stacv.mac_phy import protocols
from stacv.spi import spi_config_location
from stacv.standards import standards

PLACEHOLDER = 'FROM_DESIGN'
CLOCK_KEYS = ['name', 'port']
SIGNAL_KEYS = ['port', 'register']


class MacPhyConfig():

    def __init__(self):
        self.protocol = None
        self.filename = None
        self.location = None
        self.name = None
        self.role = None
        self.part_as_written = None
        self.traces_as_written = None
        self.timing_reports_dir = None
        # The clocks by table, and the signals the interface has, in the protocol's order; an optional signal left
        # out is not in it.
        self.clocks = {}
        self.signals = []


class Clock():

    def __init__(self):
        self.clock = None
        self.name = None
        self.port = None


class Signal():

    def __init__(self):
        self.signal = None
        self.port = None
        self.register = None


def read_mac_phy_config(sFilename, oProtocol):
    # The file has already been read as TOML by the interface reader, so it exists and is valid.
    with open(sFilename) as oFile:
        sText = oFile.read()
    oLocation = spi_config_location.SpiConfigLocation(sFilename, sText.split('\n'))
    return create_mac_phy_config(tomllib.loads(sText), oLocation, oProtocol)


def create_mac_phy_config(dConfig, oLocation, oProtocol):
    oLocation.set_table(None)
    oProtocol.reader.check_keys(dConfig, oProtocol.get_top_level_keys(), oLocation)
    oConfig = MacPhyConfig()
    oConfig.protocol = oProtocol
    oConfig.filename = oLocation.filename
    oConfig.location = oLocation
    oConfig.name = read_string(oProtocol, dConfig, None, 'name', oLocation)
    oConfig.role = read_role(oProtocol, dConfig, oLocation)
    oConfig.part_as_written = read_string(oProtocol, dConfig, None, 'part', oLocation)
    oConfig.traces_as_written = read_string(oProtocol, dConfig, None, 'traces', oLocation)
    oConfig.timing_reports_dir = read_string(oProtocol, dConfig, None, 'timing_reports_dir', oLocation)
    for oClockDescription in oProtocol.clocks:
        oConfig.clocks[oClockDescription.table] = read_clock(oProtocol, dConfig, oClockDescription, oLocation)
    for oSignalDescription in oProtocol.signals:
        if oSignalDescription.optional and oSignalDescription.table not in dConfig:
            continue
        oConfig.signals.append(read_signal(oProtocol, dConfig, oSignalDescription, oLocation))
    return oConfig


def read_string(oProtocol, dTable, sTable, sKey, oLocation):
    oLocation.set_key(sTable, sKey)
    sValue = oProtocol.reader.get_required_string(dTable, sKey, oLocation)
    if is_placeholder(sValue):
        oProtocol.reader.raise_error(6, oLocation.filename, f'key "{sKey}"{oLocation.location} is {sValue}; replace it with the name in your design')
    return sValue


def is_placeholder(sValue):
    # A template names each placeholder after the key it fills, such as FROM_DESIGN_TXD_PORT, so each can be found.
    return sValue.startswith(PLACEHOLDER)


def read_role(oProtocol, dConfig, oLocation):
    sRole = read_string(oProtocol, dConfig, None, 'role', oLocation)
    if sRole != standards.MAC:
        oProtocol.reader.raise_error(8, oLocation.filename, f'key "role"{oLocation.location} must be "{standards.MAC}"; a {standards.PHY} is not supported yet')
    return sRole


def read_table(oProtocol, dConfig, sTable, lKeys, oLocation):
    oLocation.set_key(None, sTable)
    dTable = oProtocol.reader.get_required_table(dConfig, sTable, oLocation)
    oLocation.set_table(sTable)
    oProtocol.reader.check_keys(dTable, lKeys, oLocation)
    return dTable


def read_clock(oProtocol, dConfig, oClockDescription, oLocation):
    dTable = read_table(oProtocol, dConfig, oClockDescription.table, CLOCK_KEYS, oLocation)
    oClock = Clock()
    oClock.clock = oClockDescription
    oClock.name = read_string(oProtocol, dTable, oClockDescription.table, 'name', oLocation)
    oClock.port = read_string(oProtocol, dTable, oClockDescription.table, 'port', oLocation)
    return oClock


def read_signal(oProtocol, dConfig, oSignalDescription, oLocation):
    dTable = read_table(oProtocol, dConfig, oSignalDescription.table, SIGNAL_KEYS, oLocation)
    oSignal = Signal()
    oSignal.signal = oSignalDescription
    oSignal.port = read_port(oProtocol, dTable, oSignalDescription.table, oLocation)
    oSignal.register = read_string(oProtocol, dTable, oSignalDescription.table, 'register', oLocation)
    return oSignal


def read_port(oProtocol, dTable, sTable, oLocation):
    # A bus port is written NAME[upper:lower], unlike its registers, which are written reg[*].
    sPort = read_string(oProtocol, dTable, sTable, 'port', oLocation)
    if '[' in sPort and re.fullmatch(r'[A-Za-z_]\w*\[\d+:\d+\]', sPort) is None:
        oProtocol.reader.raise_error(14, oLocation.filename, f'key "port"{oLocation.location} is {sPort}; write a bus port as NAME[upper:lower], such as TXD[1:0], and its register as reg[*]')
    return sPort


def find_part_interface(oConfig):
    # The part's interface is the one that follows the standard as the PHY.  The part file is read only once it
    # exists and is valid; until then the commands that need it stop on it, and the standard's name is used.
    oProtocol = oConfig.protocol
    dPart = read_part_file(resolve_part_path(oConfig))
    if dPart is None:
        return oProtocol.standard
    lNames = find_matching_part_interfaces(dPart, oProtocol.standard)
    if len(lNames) == 1:
        return lNames[0]
    oConfig.location.set_key(None, 'part')
    sInterfaces = f'[[interface]] with if_standard "{oProtocol.standard}" and if_role "{standards.PHY}"'
    if len(lNames) == 0:
        oProtocol.reader.raise_error(12, oConfig.filename, f'key "part"{oConfig.location.location} names {oConfig.part_as_written}, which has no {sInterfaces}')
    oProtocol.reader.raise_error(13, oConfig.filename, f'key "part"{oConfig.location.location} names {oConfig.part_as_written}, which has more than one {sInterfaces}: {", ".join(lNames)}')


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


def find_matching_part_interfaces(dPart, sStandard):
    lNames = []
    lInterfaces = dPart.get('interface')
    if not isinstance(lInterfaces, list):
        return lNames
    for dInterface in lInterfaces:
        if isinstance(dInterface, dict) and dInterface.get('if_standard') == sStandard and dInterface.get('if_role') == standards.PHY:
            lNames.append(dInterface.get('name'))
    return lNames


def build_clock_lines(oConfig):
    # The clocks, for the constraints file's references.
    lLines = []
    for oClock in oConfig.clocks.values():
        lLines.append(f'{oClock.clock.signal}  {oClock.name} {oClock.clock.period:g} ns')
    return lLines
