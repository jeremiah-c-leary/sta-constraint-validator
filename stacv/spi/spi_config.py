'''
Reads an SPI configuration file: the names in the design, the SPI mode and the edges the design moves from it.

stacv expands the file into an interface file, so a user times an SPI interface without writing the methodologies,
signals and edges that the mode already fixes.  A file with the key "interface" and no ports is an interface
configuration file.
'''

import os
import tomllib

from stacv.config import config_reader
from stacv.config import value_type
from stacv.output import number_format
from stacv.rules import edge_times
from stacv.spi import spi_config_error
from stacv.spi import spi_config_location
from stacv.spi import spi_edges
from stacv.standards import standards

READER = config_reader.ConfigReader('spi_config', spi_config_error.SpiConfigError)
INTERFACE_KEY = 'interface'
CONFIGURATIONS = ['spi']
PLACEHOLDER = 'FROM_DESIGN'
MODES = [0, 1, 2, 3]
TOP_LEVEL_KEYS = ['interface', 'name', 'mode', 'role', 'part', 'traces', 'timing_reports_dir', 'device_clock', 'sck', 'copi', 'cipo', 'cs']
DEVICE_CLOCK_KEYS = ['name', 'period']
SCK_KEYS = ['port', 'register', 'period']
DATA_KEYS = ['port', 'register', 'adjust']
CS_KEYS = ['port', 'register', 'setup_adjust', 'hold_adjust']
# The interface of a part template, used until the part file can be read.
DEFAULT_PART_INTERFACE = 'SPI'


class SpiConfig():

    def __init__(self):
        self.filename = None
        self.location = None
        self.name = None
        self.mode = None
        self.role = None
        self.part_as_written = None
        self.traces_as_written = None
        self.timing_reports_dir = None
        self.device_clock = None
        self.sck = None
        self.copi = None
        self.cipo = None
        self.cs = None
        self.standard = None
        self.edges = None


class DeviceClock():

    def __init__(self):
        self.name = None
        self.period = None


class Sck():

    def __init__(self):
        self.port = None
        self.register = None
        self.period = None


class Signal():
    # COPI, CIPO and CS: a port and the register that drives or captures it, with the edges the design moves.

    def __init__(self):
        self.port = None
        self.register = None
        self.adjust = 0
        self.setup_adjust = 0
        self.hold_adjust = 0


def is_interface_configuration(dConfig):
    # Interface files once named the interface with the key "interface", so a file with ports is an interface file.
    if 'port' in dConfig:
        return False
    return INTERFACE_KEY in dConfig


def read_spi_config(sFilename):
    # The file has already been read as TOML by the interface reader, so it exists and is valid.
    with open(sFilename) as oFile:
        sText = oFile.read()
    oLocation = spi_config_location.SpiConfigLocation(sFilename, sText.split('\n'))
    return create_spi_config(tomllib.loads(sText), oLocation)


def create_spi_config(dConfig, oLocation):
    oLocation.set_table(None)
    READER.check_keys(dConfig, TOP_LEVEL_KEYS, oLocation)
    check_configuration(dConfig, oLocation)
    oConfig = SpiConfig()
    oConfig.filename = oLocation.filename
    oConfig.location = oLocation
    oConfig.name = read_string(dConfig, None, 'name', oLocation)
    oConfig.mode = read_mode(dConfig, oLocation)
    oConfig.role = read_role(dConfig, oLocation)
    oConfig.part_as_written = read_string(dConfig, None, 'part', oLocation)
    oConfig.traces_as_written = read_string(dConfig, None, 'traces', oLocation)
    oConfig.timing_reports_dir = read_string(dConfig, None, 'timing_reports_dir', oLocation)
    oConfig.device_clock = read_device_clock(dConfig, oLocation)
    oConfig.sck = read_sck(dConfig, oLocation)
    check_sck_period(oConfig, oLocation)
    oConfig.copi = read_data_signal(dConfig, 'copi', oLocation)
    oConfig.cipo = read_data_signal(dConfig, 'cipo', oLocation)
    oConfig.cs = read_chip_select(dConfig, oLocation)
    oConfig.standard = standards.get_standard(f'SPI mode {oConfig.mode}')
    oConfig.edges = spi_edges.SpiEdges(oConfig, oConfig.standard)
    check_edges(oConfig, oLocation)
    return oConfig


def check_configuration(dConfig, oLocation):
    sConfiguration = read_string(dConfig, None, INTERFACE_KEY, oLocation)
    if sConfiguration not in CONFIGURATIONS:
        READER.raise_error(5, oLocation.filename, f'key "{INTERFACE_KEY}"{oLocation.location} names {sConfiguration}, which stacv has no configuration for; the configurations are {", ".join(CONFIGURATIONS)}')


def read_string(dTable, sTable, sKey, oLocation):
    oLocation.set_key(sTable, sKey)
    sValue = READER.get_required_string(dTable, sKey, oLocation)
    if sValue == PLACEHOLDER:
        READER.raise_error(6, oLocation.filename, f'key "{sKey}"{oLocation.location} is {PLACEHOLDER}; replace it with the name in your design')
    return sValue


def read_mode(dConfig, oLocation):
    oLocation.set_key(None, 'mode')
    iMode = READER.get_required_value_of_type(dConfig, 'mode', value_type.INTEGER, oLocation)
    if iMode not in MODES:
        READER.raise_error(7, oLocation.filename, f'key "mode"{oLocation.location} must be 0, 1, 2 or 3')
    return iMode


def read_role(dConfig, oLocation):
    sRole = read_string(dConfig, None, 'role', oLocation)
    if sRole != standards.CONTROLLER:
        READER.raise_error(8, oLocation.filename, f'key "role"{oLocation.location} must be "{standards.CONTROLLER}"; a {standards.PERIPHERAL} is not supported yet')
    return sRole


def read_table(dConfig, sTable, lKeys, oLocation):
    oLocation.set_key(None, sTable)
    dTable = READER.get_required_table(dConfig, sTable, oLocation)
    oLocation.set_table(sTable)
    READER.check_keys(dTable, lKeys, oLocation)
    return dTable


def read_period(dTable, sTable, oLocation):
    oLocation.set_key(sTable, 'period')
    fPeriod = READER.get_required_number(dTable, 'period', oLocation)
    if fPeriod <= 0:
        READER.raise_error(9, oLocation.filename, f'key "period"{oLocation.location} must be greater than 0')
    return fPeriod


def read_adjust(dTable, sTable, sKey, oLocation):
    # The mode's edges are the default, so an adjust left out is 0.
    if sKey not in dTable:
        return 0
    oLocation.set_key(sTable, sKey)
    return READER.get_required_value_of_type(dTable, sKey, value_type.INTEGER, oLocation)


def read_device_clock(dConfig, oLocation):
    dTable = read_table(dConfig, 'device_clock', DEVICE_CLOCK_KEYS, oLocation)
    oDeviceClock = DeviceClock()
    oDeviceClock.name = read_string(dTable, 'device_clock', 'name', oLocation)
    oDeviceClock.period = read_period(dTable, 'device_clock', oLocation)
    return oDeviceClock


def read_sck(dConfig, oLocation):
    dTable = read_table(dConfig, 'sck', SCK_KEYS, oLocation)
    oSck = Sck()
    oSck.port = read_string(dTable, 'sck', 'port', oLocation)
    oSck.register = read_string(dTable, 'sck', 'register', oLocation)
    oSck.period = read_period(dTable, 'sck', oLocation)
    return oSck


def read_data_signal(dConfig, sTable, oLocation):
    dTable = read_table(dConfig, sTable, DATA_KEYS, oLocation)
    oSignal = Signal()
    oSignal.port = read_string(dTable, sTable, 'port', oLocation)
    oSignal.register = read_string(dTable, sTable, 'register', oLocation)
    oSignal.adjust = read_adjust(dTable, sTable, 'adjust', oLocation)
    return oSignal


def read_chip_select(dConfig, oLocation):
    dTable = read_table(dConfig, 'cs', CS_KEYS, oLocation)
    oSignal = Signal()
    oSignal.port = read_string(dTable, 'cs', 'port', oLocation)
    oSignal.register = read_string(dTable, 'cs', 'register', oLocation)
    oSignal.setup_adjust = read_adjust(dTable, 'cs', 'setup_adjust', oLocation)
    oSignal.hold_adjust = read_adjust(dTable, 'cs', 'hold_adjust', oLocation)
    return oSignal


def check_sck_period(oConfig, oLocation):
    # Each edge of SCK is launched from a rising edge of the device clock, so SCK is an even number of its periods.
    fRatio = oConfig.sck.period / oConfig.device_clock.period
    if abs(fRatio - round(fRatio)) <= 1e-9 and round(fRatio) % 2 == 0:
        return
    oLocation.set_key('sck', 'period')
    sSck = number_format.format_number(oConfig.sck.period)
    sDeviceClock = number_format.format_number(oConfig.device_clock.period)
    READER.raise_error(10, oLocation.filename, f'key "period"{oLocation.location} is {sSck} ns, which is not an even number of device clock periods of {sDeviceClock} ns; each edge of SCK is launched from a rising edge of the device clock')


def check_edges(oConfig, oLocation):
    check_copi_edges(oConfig, oLocation)
    check_cs_edges(oConfig, oLocation)
    check_cipo_edges(oConfig, oLocation)


def check_copi_edges(oConfig, oLocation):
    oEdges = oConfig.edges
    sSample = oConfig.standard.sample_edge.lower()
    oLocation.set_key('copi', 'adjust')
    if oEdges.copi_launch < oEdges.previous_sample_edge:
        raise_edge_error(oLocation, 'adjust', f'moves the launch to edge {oEdges.copi_launch}, before the {sSample} edge of SCK at edge {oEdges.previous_sample_edge} that samples the bit before it')
    if oEdges.copi_launch >= oEdges.first_sample_edge:
        raise_edge_error(oLocation, 'adjust', f'moves the launch to edge {oEdges.copi_launch}, at or after the {sSample} edge of SCK at edge {oEdges.first_sample_edge} that samples it')


def check_cs_edges(oConfig, oLocation):
    oEdges = oConfig.edges
    sSample = oConfig.standard.sample_edge.lower()
    oLocation.set_key('cs', 'setup_adjust')
    if oEdges.cs_setup_launch < 0:
        raise_edge_error(oLocation, 'setup_adjust', f'moves the launch to edge {oEdges.cs_setup_launch}, before edge 0')
    if oEdges.cs_setup_launch >= oEdges.first_sample_edge:
        raise_edge_error(oLocation, 'setup_adjust', f'moves the launch to edge {oEdges.cs_setup_launch}, at or after the first {sSample} edge of SCK at edge {oEdges.first_sample_edge}')
    # CS is cleared after SCK stops, so only the last sample edge limits its hold launch.
    oLocation.set_key('cs', 'hold_adjust')
    if oEdges.cs_hold_launch < oEdges.previous_sample_edge:
        raise_edge_error(oLocation, 'hold_adjust', f'moves the launch to edge {oEdges.cs_hold_launch}, before the last {sSample} edge of SCK at edge {oEdges.previous_sample_edge}')


def check_cipo_edges(oConfig, oLocation):
    # The captures are on the device clock, so they are its letters, and so is the edge of SCK that launches CIPO.
    oEdges = oConfig.edges
    sChange = oConfig.standard.change_edge.lower()
    sLaunch = edge_times.convert_edge_number_to_letter(oEdges.change_edge)
    oLocation.set_key('cipo', 'adjust')
    if oEdges.cipo_hold_capture < 0:
        raise_edge_error(oLocation, 'adjust', 'moves the hold capture before edge A, the first edge')
    if oEdges.cipo_setup_capture <= oEdges.change_edge:
        raise_edge_error(oLocation, 'adjust', f'moves the setup capture to edge {edge_times.convert_edge_number_to_letter(oEdges.cipo_setup_capture)}, at or before the {sChange} edge of SCK at edge {sLaunch} that launches CIPO')
    if oEdges.cipo_hold_capture > oEdges.change_edge:
        raise_edge_error(oLocation, 'adjust', f'moves the hold capture to edge {edge_times.convert_edge_number_to_letter(oEdges.cipo_hold_capture)}, after the {sChange} edge of SCK at edge {sLaunch} that launches CIPO')


def raise_edge_error(oLocation, sKey, sMessage):
    READER.raise_error(11, oLocation.filename, f'key "{sKey}"{oLocation.location} {sMessage}')


def find_part_interface(oConfig):
    # The part's SPI interface is the one that follows the mode as the peripheral.  The part file is read only once it
    # exists and is valid; until then the commands that need it stop on it.
    dPart = read_part_file(resolve_part_path(oConfig))
    if dPart is None:
        return DEFAULT_PART_INTERFACE
    lNames = find_matching_part_interfaces(dPart, oConfig)
    if len(lNames) == 1:
        return lNames[0]
    oConfig.location.set_key(None, 'part')
    sInterfaces = f'[[interface]] with if_standard "{oConfig.standard.name}" and if_role "{standards.PERIPHERAL}"'
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


def find_matching_part_interfaces(dPart, oConfig):
    lNames = []
    lInterfaces = dPart.get('interface')
    if not isinstance(lInterfaces, list):
        return lNames
    for dInterface in lInterfaces:
        if is_matching_part_interface(dInterface, oConfig):
            lNames.append(dInterface.get('name'))
    return lNames


def is_matching_part_interface(dInterface, oConfig):
    if not isinstance(dInterface, dict):
        return False
    if dInterface.get('if_standard') != oConfig.standard.name:
        return False
    return dInterface.get('if_role') == standards.PERIPHERAL


def describe_edges(oConfig):
    # Until a simulation checks them, the edges are the mode's defaults moved by the adjusts the user gave.
    lParts = [f'SPI mode {oConfig.mode} defaults']
    lParts.extend(describe_adjusts(oConfig))
    lParts.append('not verified against simulation')
    return '; '.join(lParts)


def describe_adjusts(oConfig):
    lAdjusts = []
    if oConfig.copi.adjust != 0:
        lAdjusts.append(f'COPI {oConfig.copi.adjust:+d}')
    lChipSelect = []
    if oConfig.cs.setup_adjust != 0:
        lChipSelect.append(f'setup {oConfig.cs.setup_adjust:+d}')
    if oConfig.cs.hold_adjust != 0:
        lChipSelect.append(f'hold {oConfig.cs.hold_adjust:+d}')
    if len(lChipSelect) > 0:
        lAdjusts.append('CS ' + ', '.join(lChipSelect))
    if oConfig.cipo.adjust != 0:
        lAdjusts.append(f'CIPO {oConfig.cipo.adjust:+d}')
    return lAdjusts
