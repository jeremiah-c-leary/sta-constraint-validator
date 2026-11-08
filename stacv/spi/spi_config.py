'''
Reads an SPI configuration file: the names in the design, the SPI mode, and the edges the design launches and captures
each signal on, counted in device clocks from an edge of SCK.

stacv expands the file into an interface file, so a user times an SPI interface without writing the methodologies,
signals and edges that the mode already fixes.  A file with the key "interface" and no ports is an interface
configuration file.
'''

import os
import tomllib

from stacv.config import config_reader
from stacv.config import value_type
from stacv.output import number_format
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
SCK_KEYS = ['port', 'register', 'period', 'read_period']
COPI_KEYS = ['port', 'register', 'launch']
CIPO_KEYS = ['port', 'register', 'capture']
CS_KEYS = ['port', 'register', 'assert', 'deassert']
EDGE_KEYS = ['sck_edge', 'clocks', 'source']
# The SCK edge each edge key is counted from, in the order the template offers them.
SCK_EDGES = {}
SCK_EDGES['launch'] = ['change']
SCK_EDGES['capture'] = ['sample']
SCK_EDGES['assert'] = ['first sample']
SCK_EDGES['deassert'] = ['last change', 'last sample']
# A device clock period has two edges, so an edge is half a clock.
EDGES_PER_CLOCK = 2
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
        # A slower SCK for reads, which CIPO is timed on; None when reads run at the same period.
        self.read_period = None

    def find_read_period(self):
        if self.read_period is None:
            return self.period
        return self.read_period


class Signal():
    # COPI, CIPO and CS: a port, the register that drives or captures it, and the edges it is launched or captured on.

    def __init__(self):
        self.port = None
        self.register = None
        self.edges = {}


class Edge():
    # Where the design launches or captures a signal: a number of device clocks from an edge of SCK, and why.

    def __init__(self):
        self.key = None
        self.sck_edge = None
        self.clocks = None
        self.source = None

    def count_device_clock_edges(self):
        return round(self.clocks * EDGES_PER_CLOCK)


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
    oConfig.copi = read_signal(dConfig, 'copi', COPI_KEYS, oLocation)
    oConfig.cipo = read_signal(dConfig, 'cipo', CIPO_KEYS, oLocation)
    oConfig.cs = read_signal(dConfig, 'cs', CS_KEYS, oLocation)
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


def read_period(dTable, sTable, sKey, oLocation):
    oLocation.set_key(sTable, sKey)
    fPeriod = READER.get_required_number(dTable, sKey, oLocation)
    if fPeriod <= 0:
        READER.raise_error(9, oLocation.filename, f'key "{sKey}"{oLocation.location} must be greater than 0')
    return fPeriod


def read_device_clock(dConfig, oLocation):
    dTable = read_table(dConfig, 'device_clock', DEVICE_CLOCK_KEYS, oLocation)
    oDeviceClock = DeviceClock()
    oDeviceClock.name = read_string(dTable, 'device_clock', 'name', oLocation)
    oDeviceClock.period = read_period(dTable, 'device_clock', 'period', oLocation)
    return oDeviceClock


def read_sck(dConfig, oLocation):
    dTable = read_table(dConfig, 'sck', SCK_KEYS, oLocation)
    oSck = Sck()
    oSck.port = read_string(dTable, 'sck', 'port', oLocation)
    oSck.register = read_string(dTable, 'sck', 'register', oLocation)
    oSck.period = read_period(dTable, 'sck', 'period', oLocation)
    if 'read_period' in dTable:
        oSck.read_period = read_period(dTable, 'sck', 'read_period', oLocation)
    return oSck


def read_signal(dConfig, sTable, lKeys, oLocation):
    # The keys after port and register are the signal's edges.
    dTable = read_table(dConfig, sTable, lKeys, oLocation)
    oSignal = Signal()
    oSignal.port = read_string(dTable, sTable, 'port', oLocation)
    oSignal.register = read_string(dTable, sTable, 'register', oLocation)
    for sKey in lKeys[2:]:
        oSignal.edges[sKey] = read_edge(dTable, sTable, sKey, oLocation)
    return oSignal


def read_edge(dTable, sTable, sKey, oLocation):
    oLocation.set_key(sTable, sKey)
    dEdge = READER.get_required_table(dTable, sKey, oLocation)
    READER.check_keys(dEdge, EDGE_KEYS, oLocation)
    oEdge = Edge()
    oEdge.key = sKey
    oEdge.sck_edge = read_sck_edge(dEdge, sKey, oLocation)
    oEdge.clocks = read_clocks(dEdge, sKey, oLocation)
    oEdge.source = read_edge_source(dEdge, sKey, oLocation)
    return oEdge


def read_sck_edge(dEdge, sKey, oLocation):
    sSckEdge = READER.get_required_string(dEdge, 'sck_edge', oLocation)
    lSckEdges = SCK_EDGES[sKey]
    if sSckEdge not in lSckEdges:
        READER.raise_error(14, oLocation.filename, f'key "{sKey}"{oLocation.location} has sck_edge "{sSckEdge}"; it must be {describe_choices(lSckEdges)}')
    return sSckEdge


def describe_choices(lChoices):
    lQuoted = []
    for sChoice in lChoices:
        lQuoted.append(f'"{sChoice}"')
    return ' or '.join(lQuoted)


def read_clocks(dEdge, sKey, oLocation):
    # A design can launch on the falling edge of the device clock, half a clock from a rising edge.
    fClocks = READER.get_required_number(dEdge, 'clocks', oLocation)
    fEdges = fClocks * EDGES_PER_CLOCK
    if abs(fEdges - round(fEdges)) > 1e-9:
        READER.raise_error(15, oLocation.filename, f'key "{sKey}"{oLocation.location} has clocks {number_format.format_number(fClocks)}; an edge is on a device clock edge, so clocks is a whole or half number')
    return fClocks


def read_edge_source(dEdge, sKey, oLocation):
    # The edges are the judgement in the file, so each one says where in the design it comes from.
    sSource = READER.get_required_string(dEdge, 'source', oLocation)
    if sSource == PLACEHOLDER:
        READER.raise_error(6, oLocation.filename, f'key "{sKey}"{oLocation.location} has source {PLACEHOLDER}; say where in the design the edge comes from')
    return sSource


def check_sck_period(oConfig, oLocation):
    check_even_number_of_device_clocks(oConfig, 'period', oConfig.sck.period, oLocation)
    if oConfig.sck.read_period is not None:
        check_even_number_of_device_clocks(oConfig, 'read_period', oConfig.sck.read_period, oLocation)


def check_even_number_of_device_clocks(oConfig, sKey, fPeriod, oLocation):
    # Each edge of SCK is launched from a rising edge of the device clock, so SCK is an even number of its periods.
    fRatio = fPeriod / oConfig.device_clock.period
    if abs(fRatio - round(fRatio)) <= 1e-9 and round(fRatio) % 2 == 0:
        return
    oLocation.set_key('sck', sKey)
    sSck = number_format.format_number(fPeriod)
    sDeviceClock = number_format.format_number(oConfig.device_clock.period)
    READER.raise_error(10, oLocation.filename, f'key "{sKey}"{oLocation.location} is {sSck} ns, which is not an even number of device clock periods of {sDeviceClock} ns; each edge of SCK is launched from a rising edge of the device clock')


def check_edges(oConfig, oLocation):
    check_copi_edges(oConfig, oLocation)
    check_cs_edges(oConfig, oLocation)
    check_cipo_edges(oConfig, oLocation)


def check_copi_edges(oConfig, oLocation):
    oEdges = oConfig.edges
    sSample = oConfig.standard.sample_edge.lower()
    oLocation.set_key('copi', 'launch')
    if oEdges.copi_launch < oEdges.previous_sample_edge:
        raise_edge_error(oLocation, 'launch', f'puts the launch at edge {oEdges.copi_launch}, before the {sSample} edge of SCK at edge {oEdges.previous_sample_edge} that samples the bit before it')
    if oEdges.copi_launch >= oEdges.first_sample_edge:
        raise_edge_error(oLocation, 'launch', f'puts the launch at edge {oEdges.copi_launch}, at or after the {sSample} edge of SCK at edge {oEdges.first_sample_edge} that samples it')


def check_cs_edges(oConfig, oLocation):
    oEdges = oConfig.edges
    sSample = oConfig.standard.sample_edge.lower()
    oLocation.set_key('cs', 'assert')
    if oEdges.cs_setup_launch < 0:
        raise_edge_error(oLocation, 'assert', f'puts the launch at edge {oEdges.cs_setup_launch}, before edge 0')
    if oEdges.cs_setup_launch >= oEdges.first_sample_edge:
        raise_edge_error(oLocation, 'assert', f'puts the launch at edge {oEdges.cs_setup_launch}, at or after the first {sSample} edge of SCK at edge {oEdges.first_sample_edge}')
    # CS is cleared after SCK stops, so only the last sample edge limits its hold launch.
    oLocation.set_key('cs', 'deassert')
    if oEdges.cs_hold_launch < oEdges.previous_sample_edge:
        raise_edge_error(oLocation, 'deassert', f'puts the launch at edge {oEdges.cs_hold_launch}, before the last {sSample} edge of SCK at edge {oEdges.previous_sample_edge}')


def check_cipo_edges(oConfig, oLocation):
    # The captures are numbered on the device clock, and so is the edge of SCK that launches CIPO.
    oEdges = oConfig.edges
    sChange = oConfig.standard.change_edge.lower()
    iLaunch = oEdges.cipo_change_edge
    oLocation.set_key('cipo', 'capture')
    if oEdges.cipo_hold_capture < 0:
        raise_edge_error(oLocation, 'capture', 'puts the hold capture before edge 0, the first edge')
    if oEdges.cipo_setup_capture <= oEdges.cipo_change_edge:
        raise_edge_error(oLocation, 'capture', f'puts the setup capture at edge {oEdges.cipo_setup_capture}, at or before the {sChange} edge of SCK at edge {iLaunch} that launches CIPO')
    if oEdges.cipo_hold_capture > oEdges.cipo_change_edge:
        raise_edge_error(oLocation, 'capture', f'puts the hold capture at edge {oEdges.cipo_hold_capture}, after the {sChange} edge of SCK at edge {iLaunch} that launches CIPO')


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


EDGE_ROWS = [('COPI launch', 'copi', 'launch'), ('CIPO capture', 'cipo', 'capture'), ('CS assert', 'cs', 'assert'), ('CS deassert', 'cs', 'deassert')]
# How each SCK edge reads in a sentence.
SCK_EDGE_NAMES = {}
SCK_EDGE_NAMES['change'] = 'the SCK change edge'
SCK_EDGE_NAMES['sample'] = 'the SCK sample edge'
SCK_EDGE_NAMES['first sample'] = 'the first SCK sample edge'
SCK_EDGE_NAMES['last change'] = 'the last SCK change edge'
SCK_EDGE_NAMES['last sample'] = 'the last SCK sample edge'
EDGES_HEADING = 'set in the SPI configuration, not verified against simulation'


def build_edge_lines(oConfig):
    # Until a simulation checks them, the edges are the ones the configuration gives, each with its source.
    lRows = []
    for sName, sTable, sKey in EDGE_ROWS:
        oEdge = getattr(oConfig, sTable).edges[sKey]
        lRows.append((sName, describe_edge(oEdge), oEdge.source))
    iNameWidth = find_column_width(lRows, 0)
    iWhereWidth = find_column_width(lRows, 1)
    lLines = []
    for sName, sWhere, sSource in lRows:
        lLines.append(f'{sName.ljust(iNameWidth)}  {sWhere.ljust(iWhereWidth)}  {sSource}')
    return lLines


def find_column_width(lRows, iColumn):
    iWidth = 0
    for tRow in lRows:
        iWidth = max(iWidth, len(tRow[iColumn]))
    return iWidth


def describe_edge(oEdge):
    sSckEdge = SCK_EDGE_NAMES[oEdge.sck_edge]
    if oEdge.clocks == 0:
        return f'at {sSckEdge}'
    sClocks = describe_clocks(abs(oEdge.clocks))
    if oEdge.clocks < 0:
        return f'{sClocks} before {sSckEdge}'
    return f'{sClocks} after {sSckEdge}'


def describe_clocks(fClocks):
    sNumber = number_format.format_number(fClocks)
    if fClocks == 1:
        return f'{sNumber} clock'
    return f'{sNumber} clocks'
