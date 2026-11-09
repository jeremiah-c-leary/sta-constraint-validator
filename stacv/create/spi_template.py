'''
Creates the SPI configuration, part and traces files of an SPI interface, linked by the signals of the SPI standard.

The user fills in the names in the design in the SPI configuration, the part's timing from its datasheet, and the trace
delays.  stacv works out every edge from the mode and the clock periods, and expands the configuration into an
interface file whenever a command reads it.
'''

from stacv.create import create_error
from stacv.output import number_format
from stacv.part import part
from stacv.spi import spi_config
from stacv.standards import standards

FILE_NAMES = ['spi_config.toml', 'part.toml', 'traces.toml']
DESIGN_PLACEHOLDER = spi_config.PLACEHOLDER
DOCS_URL = 'https://github.com/jeremiah-c-leary/sta-constraint-validator/blob/main/docs/source'
PLACEHOLDER = part.PLACEHOLDER
WIRES = [3, 4]
DIVIDER = '#--- set by stacv create template spi; do not change below ---'
TYPES = [standards.CONTROLLER, standards.PERIPHERAL]


class SpiOptions():
    '''
    The command line options of an SPI template.
    '''

    def __init__(self, iWires, iMode, sType, fClockPeriod, fSckPeriod):
        self.wires = iWires
        self.mode = iMode
        self.type = sType
        self.clock_period = fClockPeriod
        self.sck_period = fSckPeriod


def check_options(oOptions):
    if oOptions.wires == 3:
        raise create_error.CreateError('create_004', '--wires 3 is not supported yet; 3-wire SPI shares one data line, SDIO, in both directions')
    if oOptions.type == standards.PERIPHERAL:
        raise create_error.CreateError('create_004', '--type peripheral is not supported yet; the chip select of a peripheral is timed to a clock from the part')
    if oOptions.clock_period <= 0 or oOptions.sck_period <= 0:
        raise create_error.CreateError('create_005', '--clock-period and --sck-period must be greater than 0')
    fRatio = oOptions.sck_period / oOptions.clock_period
    if abs(fRatio - round(fRatio)) > 1e-9 or round(fRatio) % 2 != 0:
        raise create_error.CreateError('create_005', f'--sck-period {format_period(oOptions.sck_period)} is not an even number of --clock-period {format_period(oOptions.clock_period)}; each edge of SCK is launched from a rising edge of the device clock')


def create_files(oOptions):
    # The three files, by name.
    check_options(oOptions)
    oStandard = standards.get_standard(f'SPI mode {oOptions.mode}')
    dFiles = {}
    dFiles['spi_config.toml'] = build_spi_config(oOptions, oStandard)
    dFiles['part.toml'] = build_part(oOptions, oStandard)
    dFiles['traces.toml'] = build_traces(oOptions)
    return dFiles


def build_command(oOptions):
    return f'stacv create template spi --wires {oOptions.wires} --mode {oOptions.mode} --type {oOptions.type} --clock-period {format_period(oOptions.clock_period)} --sck-period {format_period(oOptions.sck_period)}'


def describe_mode(oStandard):
    return f'SCK idles {oStandard.idle}, data changes on the {oStandard.change_edge.lower()} edge and is sampled on the {oStandard.sample_edge.lower()} edge.'


def build_divider():
    # The keys below it are set from the command line, so they are changed by creating the files again.
    return DIVIDER


def build_header_divider_lines():
    lLines = []
    lLines.append('# Keys below each "set by stacv create template spi" line are set from the command line above;')
    lLines.append('# create the files again to change them.')
    return lLines


def build_spi_config(oOptions, oStandard):
    lLines = []
    lLines.append(f'# stacv SPI configuration file for a {oOptions.wires}-wire SPI interface, SPI mode {oOptions.mode}, with the device as the {oOptions.type}.')
    lLines.append(f'# Created by:  {build_command(oOptions)}')
    lLines.append('#')
    lLines.append('# Keys are described in:')
    lLines.append(f'# {DOCS_URL}/spi_config.rst')
    lLines.append('#')
    lLines.append('# stacv generates the interface file, the constraints and the report script')
    lLines.append('# from this file.  Only this file, the part file and the traces file are edited.')
    lLines.append('#')
    lLines.append(f'# Replace each {DESIGN_PLACEHOLDER}_... with the name in your design; stacv stops on it until then.')
    lLines.append('# Each placeholder is named after its key, so it can be found and replaced on its own.')
    lLines.append('# Registers are named as Vivado names them:  the hierarchy separated by /, with')
    lLines.append('# _reg added, and a bit of a bus in brackets, such as u_spi/rx_shift_reg[0].')
    lLines.append('#')
    lLines.append(f'# SPI mode {oOptions.mode}:  {describe_mode(oStandard)}')
    lLines.append('#')
    lLines.append('# Edges:  each launch and capture is counted in device clocks from a named edge')
    lLines.append('#         of SCK, as the HDL counts them:  -4 is four device clock periods before')
    lLines.append('#         that edge, 0.5 half a period after it (a register on the falling edge).')
    lLines.append('#         The values below are the usual ones for the mode; read the HDL, correct')
    lLines.append('#         them, and say in source where each comes from.  Check them with:')
    lLines.append('#             stacv visualize edges spi_config.toml')
    lLines.append('#         A negative hold requirement in the drawing means the signal changes')
    lLines.append('#         after the edge that captures it.')
    lLines.append('#')
    lLines.append('# Periods are in nanoseconds.  Paths are relative to this file.')
    lLines.append('')
    lLines.append('interface = "spi"')
    lLines.append('name      = "SPI"')
    lLines.append(f'mode      = {oOptions.mode}')
    lLines.append(f'role      = "{oOptions.type}"')
    lLines.append('')
    lLines.append('part    = "part.toml"')
    lLines.append('traces  = "traces.toml"')
    lLines.append('')
    lLines.append('timing_reports_dir = "timing_reports"')
    lLines.append('')
    lLines.append('# The device clock the SPI logic runs on.')
    lLines.append('[device_clock]')
    lLines.append(f'name   = "{build_design_placeholder("device_clock", "name")}"')
    lLines.append(f'period = {format_config_period(oOptions.clock_period)}')
    lLines.append('# source = "<where the period comes from>"   # optional')
    lLines.append('')
    lLines.append('# SCK, the SPI clock: generated in the device by a register and forwarded to the part.')
    lLines.append('[sck]')
    lLines.append(f'port     = "{build_design_placeholder("sck", "port")}"')
    lLines.append(f'register = "{build_design_placeholder("sck", "register")}"')
    lLines.append(f'period   = {format_config_period(oOptions.sck_period)}')
    lLines.append('# read_period = <ns>   # a slower SCK for reads, when the part\'s CIPO needs one;')
    lLines.append('#                      # COPI and CS are then timed on SCK, and CIPO on the read SCK')
    lLines.append('# source = "<where the periods come from>"   # optional')
    lLines.append('')
    lLines.extend(build_copi(oOptions, oStandard))
    lLines.append('')
    lLines.extend(build_cipo(oOptions, oStandard))
    lLines.append('')
    lLines.extend(build_cs(oOptions, oStandard))
    return lLines


def build_copi(oOptions, oStandard):
    sChange = oStandard.change_edge.lower()
    sSample = oStandard.sample_edge.lower()
    lLines = []
    lLines.append('# COPI: data from the device into the part.')
    lLines.append(f'#   launch:   when the design changes COPI, from the SCK change edge ({sChange})')
    lLines.append(f'#             {format_period(oOptions.sck_period / 2)} ns before the {sSample} sample edge that captures it.')
    lLines.append('[copi]')
    lLines.append(f'port     = "{build_design_placeholder("copi", "port")}"')
    lLines.append(f'register = "{build_design_placeholder("copi", "register")}"')
    lLines.append(f'launch   = {build_edge("copi", "launch", "change", 0)}')
    return lLines


def build_cipo(oOptions, oStandard):
    sChange = oStandard.change_edge.lower()
    sSample = oStandard.sample_edge.lower()
    lLines = []
    lLines.append('# CIPO: data from the part into the device.')
    lLines.append(f'#   capture:  when the device captures CIPO, from the SCK sample edge ({sSample})')
    lLines.append(f'#             {format_period(oOptions.sck_period / 2)} ns after the {sChange} change edge the part launches it on.')
    lLines.append('#             0 is the device clock edge that makes that SCK edge.')
    lLines.append('[cipo]')
    lLines.append(f'port     = "{build_design_placeholder("cipo", "port")}"')
    lLines.append(f'register = "{build_design_placeholder("cipo", "register")}"')
    lLines.append(f'capture  = {build_edge("cipo", "capture", "sample", 0)}')
    return lLines


def build_cs(oOptions, oStandard):
    sSample = oStandard.sample_edge.lower()
    sChange = oStandard.change_edge.lower()
    sSckClocks = format_period(oOptions.sck_period / oOptions.clock_period)
    lLines = []
    lLines.append(f'# CS: selects the part.  Timed to the first and last {sSample} edges of SCK.')
    lLines.append('#   assert:   when CS becomes active, from the first SCK sample edge;')
    lLines.append(f'#             -{sSckClocks} is one SCK period ({format_period(oOptions.sck_period)} ns) before it.')
    lLines.append(f'#   deassert: when CS becomes inactive, from the last SCK change edge ({sChange}),')
    lLines.append('#             or with sck_edge = "last sample", from the last sample edge.')
    lLines.append('#             The drawing measures the hold from the last sample edge either way.')
    lLines.append('#   With read_period, give the access with the least time to the SCK edge: usually')
    lLines.append('#   the faster write, as CS is timed on SCK, not on the read SCK.')
    lLines.append('[cs]')
    lLines.append(f'port     = "{build_design_placeholder("cs", "port")}"')
    lLines.append(f'register = "{build_design_placeholder("cs", "register")}"')
    lLines.append(f'assert   = {build_edge("cs", "assert", "first sample", -1 * oOptions.sck_period / oOptions.clock_period)}')
    lLines.append(f'deassert = {build_edge("cs", "deassert", "last change", 0)}')
    return lLines


def build_edge(sTable, sKey, sSckEdge, fClocks):
    sSource = build_design_placeholder(sTable, sKey, 'source')
    return f'{{sck_edge = "{sSckEdge}", clocks = {format_period(fClocks)}, source = "{sSource}"}}'


def build_design_placeholder(*lNames):
    # Named after the table and key it fills, such as FROM_DESIGN_SCK_PORT.
    return build_placeholder_name(DESIGN_PLACEHOLDER, lNames)


def build_datasheet_placeholder(*lNames):
    return build_placeholder_name(PLACEHOLDER, lNames)


def build_placeholder_name(sPrefix, lNames):
    lParts = [sPrefix]
    for sName in lNames:
        lParts.append(sName.upper().replace(' ', '_'))
    return '_'.join(lParts)


def format_config_period(fPeriod):
    # A period is written as the number given, always with a decimal point, as a time.
    return str(float(fPeriod))


def build_part(oOptions, oStandard):
    lLines = []
    lLines.append(f'# stacv part file for the peripheral of a {oOptions.wires}-wire SPI interface, SPI mode {oOptions.mode}.')
    lLines.append(f'# Created by:  {build_command(oOptions)}')
    lLines.append('#')
    lLines.append('# Keys are described in:')
    lLines.append(f'# {DOCS_URL}/part.rst')
    lLines.append('#')
    lLines.append('# Fill in each value from the part\'s datasheet, with its symbol and where it comes from,')
    lLines.append('# such as source = "SBASAO8A section 6.9, page 27": the document, its section and page.')
    lLines.append(f'# The values are {PLACEHOLDER}_... until then, each named after its key, which stacv stops on.')
    lLines.append('# stacv does not check the SCK period, its high and low times, or the gap CS must stay')
    lLines.append('# high between accesses (such as tP, tPH, tPL and tIAG), and max_frequency is recorded')
    lLines.append('# but not yet checked: check those by hand against the design.')
    lLines.append('# Rename the pins to the datasheet\'s; the traces file keeps its trace names, as the')
    lLines.append('# files are linked by signal, not by name.')
    lLines.extend(build_header_divider_lines())
    lLines.append('#')
    lLines.append('# All delays are in nanoseconds.')
    lLines.append('# All frequencies are in MHz.')
    lLines.append('')
    lLines.append('[properties]')
    lLines.append(f'manufacturer = "{build_datasheet_placeholder("manufacturer")}"')
    lLines.append(f'part_number = "{build_datasheet_placeholder("part_number")}"')
    lLines.append('')
    lLines.append('[datasheet]')
    lLines.append(f'name = "{build_datasheet_placeholder("datasheet", "name")}"')
    lLines.append(f'url = "{build_datasheet_placeholder("datasheet", "url")}"')
    lLines.append(f'version = "{build_datasheet_placeholder("datasheet", "version")}"')
    lLines.append('')
    lLines.append('[[interface]]')
    lLines.append('name = "SPI"')
    lLines.append(build_divider())
    lLines.append(f'if_standard = "{oStandard.name}"')
    lLines.append(f'if_role = "{oStandard.get_other_role(oOptions.type)}"')
    lLines.append('')
    lLines.append('[[interface.clock_pin]]')
    lLines.append('name = "SCK"')
    lLines.append(build_divider())
    lLines.append('if_signal = "SCK"')
    lLines.append('')
    lLines.append(f'# COPI: setup and hold, measured to the SCK sample edge ({oStandard.sample_edge.lower()}), such as tSU and tH.')
    lLines.extend(build_input_pin('COPI', oStandard.sample_edge))
    lLines.append('')
    lLines.append(f'# CS: setup to the first SCK sample edge ({oStandard.sample_edge.lower()}) and hold after the last, such as tCSS and tCSH.')
    lLines.extend(build_input_pin('CS', oStandard.sample_edge))
    lLines.append('')
    lLines.append(f'# CIPO: clock to out, measured from the SCK change edge ({oStandard.change_edge.lower()}) to CIPO valid, such as tOD or tCO.')
    lLines.append('# When the datasheet also gives the time to drive CIPO out of high impedance (such as tOZD),')
    lLines.append('# use the worse of the two, as the first bit of a read is driven from high impedance.')
    lLines.append('[[interface.pin]]')
    lLines.append('name = "CIPO"')
    lLines.append(build_placeholder('CIPO', 'cko_max'))
    lLines.append(build_placeholder('CIPO', 'cko_min'))
    lLines.append(build_clock('CIPO'))
    lLines.append(build_divider())
    lLines.append('methodology = "SDR-SS-RT-DO"')
    lLines.append('if_signal = "CIPO"')
    lLines.append(f'launch_edge = "{oStandard.change_edge}"')
    return lLines


def build_input_pin(sName, sCaptureEdge):
    lLines = []
    lLines.append('[[interface.pin]]')
    lLines.append(f'name = "{sName}"')
    lLines.append(build_placeholder(sName, 'setup'))
    lLines.append(build_placeholder(sName, 'hold'))
    lLines.append(build_clock(sName))
    lLines.append(build_divider())
    lLines.append('methodology = "SDR-SS-I"')
    lLines.append(f'if_signal = "{sName}"')
    lLines.append(f'capture_edge = "{sCaptureEdge}"')
    return lLines


def build_clock(sPin):
    # The fastest SCK the part's pin allows is a datasheet value.
    return f'clock = {{if_signal = "SCK", max_frequency = "{build_datasheet_placeholder(sPin, "max_frequency")}"}}'


def build_placeholder(sPin, sKey):
    # The value, its symbol and where it comes from are all the datasheet's, so each is filled in from it.
    sValue = build_datasheet_placeholder(sPin, sKey, 'value')
    sSymbol = build_datasheet_placeholder(sPin, sKey, 'symbol')
    sSource = build_datasheet_placeholder(sPin, sKey, 'source')
    return f'{sKey} = {{value = "{sValue}", symbol = "{sSymbol}", source = "{sSource}"}}'


def build_traces(oOptions):
    lLines = []
    lLines.append(f'# stacv traces file for a {oOptions.wires}-wire SPI interface, with the device as the {oOptions.type}.')
    lLines.append(f'# Created by:  {build_command(oOptions)}')
    lLines.append('#')
    lLines.append('# Keys are described in:')
    lLines.append(f'# {DOCS_URL}/traces.rst')
    lLines.append('#')
    lLines.append('# Fill in each trace\'s delays from the board, or leave {} to use default_delay.')
    lLines.append('# The trace names stay as they are when the part\'s pins are renamed: each trace is')
    lLines.append('# linked to its port and pin by its signal.')
    lLines.extend(build_header_divider_lines())
    lLines.append('#')
    lLines.append('# Delays are in nanoseconds.')
    lLines.append('')
    lLines.append('default_delay = {max_delay = 1.00, min_delay = 0.00}')
    for sSignal, sDirection in [('SCK', 'device_to_part'), ('COPI', 'device_to_part'), ('CIPO', 'part_to_device'), ('CS', 'device_to_part')]:
        lLines.append('')
        lLines.append('[[trace]]')
        lLines.append(f'name = "{sSignal.lower()}"')
        lLines.append(f'{sDirection} = {{}}')
        lLines.append(build_divider())
        lLines.append(f'if_signal = "{sSignal}"')
    return lLines


def format_period(fPeriod):
    return number_format.format_number(fPeriod)
