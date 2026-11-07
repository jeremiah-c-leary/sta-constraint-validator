'''
Creates the interface, part and traces files of an SPI interface, linked by the signals of the SPI standard.

The mode sets the level SCK idles at and the edges data changes and is sampled on, and the clock periods set where
those edges are, so every launch and capture edge is worked out here.  The user fills in the part's timing from its
datasheet, the registers, and the trace delays, and checks the edges with stacv visualize edges.

The edges, with SCK half a period, H, long and divided from the device clock:

    COPI   launched with the change edge before the first sample edge, captured on the sample edges either side of it
    CS     timed to the first and last sample edges: set one SCK period before the first, cleared at the change edge
           after the last
    CIPO   launched by the part on SCK's change edge, captured by the device at the sample edges either side of it
'''

from stacv.create import create_error
from stacv.output import number_format
from stacv.part import part
from stacv.standards import standards

FILE_NAMES = ['interface.toml', 'part.toml', 'traces.toml']
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


class SpiEdges():
    '''
    The launch and capture edges of each port, for the mode and the clock periods.
    '''

    def __init__(self, oOptions, oStandard):
        iClockEdgesPerSckEdge = round(oOptions.sck_period / oOptions.clock_period)
        self.sample_edge = oStandard.sample_edge
        self.change_edge = oStandard.change_edge
        # SCK rises at its edge 0, A, and falls at its edge 1, B.  The first sample edge is the first of the sample
        # kind after edge 0, so there is a change edge before it to launch on.
        iFirstSample = 2
        if oStandard.sample_edge == standards.FALLING:
            iFirstSample = 3
        iChange = iFirstSample - 1
        self.copi_launch = iChange * iClockEdgesPerSckEdge
        self.copi_setup_capture = convert_number_to_letter(iFirstSample)
        self.copi_hold_capture = convert_number_to_letter(iFirstSample - 2)
        self.cs_setup_launch = (iFirstSample - 2) * iClockEdgesPerSckEdge
        self.cs_hold_launch = self.copi_launch
        self.cipo_launch = iChange
        self.cipo_setup_capture = convert_number_to_letter(iFirstSample * iClockEdgesPerSckEdge)
        self.cipo_hold_capture = convert_number_to_letter((iFirstSample - 2) * iClockEdgesPerSckEdge)


def convert_number_to_letter(iEdgeNumber):
    sLetters = ''
    iRemaining = iEdgeNumber + 1
    while iRemaining > 0:
        iRemaining, iLetter = divmod(iRemaining - 1, 26)
        sLetters = chr(ord('A') + iLetter) + sLetters
    return sLetters


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
    oEdges = SpiEdges(oOptions, oStandard)
    dFiles = {}
    dFiles['interface.toml'] = build_interface(oOptions, oStandard, oEdges)
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


def build_interface(oOptions, oStandard, oEdges):
    sChange = oStandard.change_edge.lower()
    sSample = oStandard.sample_edge.lower()
    lLines = []
    lLines.append(f'# stacv interface file for a {oOptions.wires}-wire SPI interface, SPI mode {oOptions.mode}, with the device as the {oOptions.type}.')
    lLines.append(f'# Created by:  {build_command(oOptions)}')
    lLines.append('#')
    lLines.append('# Keys are described in:')
    lLines.append(f'# {DOCS_URL}/interface.rst')
    lLines.append('# The SPI signals and modes are described in:')
    lLines.append(f'# {DOCS_URL}/standards.rst')
    lLines.append('#')
    lLines.append('# Rename the clocks, ports and registers to your design\'s, and SPI_INTERFACE_NAME everywhere it appears.')
    lLines.extend(build_header_divider_lines())
    lLines.append('# Check the edges against the part\'s datasheet with:  stacv visualize edges interface.toml')
    lLines.append('#')
    lLines.append(f'# SPI mode {oOptions.mode}:  {describe_mode(oStandard)}')
    lLines.append('#')
    lLines.append('# Paths are relative to this file.')
    lLines.append('#')
    lLines.append('# All periods are in nanoseconds.')
    lLines.append('')
    lLines.append('description = "SPI_DESCRIPTION"')
    lLines.append('name = "SPI_INTERFACE_NAME"')
    lLines.append('part = "part.toml"')
    lLines.append('part_interface = "SPI"')
    lLines.append('traces = "traces.toml"')
    lLines.append(build_divider())
    lLines.append(f'if_standard = "{oStandard.name}"')
    lLines.append(f'if_role = "{oOptions.type}"')
    lLines.append('')
    lLines.append('# The device clock the SPI logic runs on.')
    lLines.append('[[clock]]')
    lLines.append('name = "device_clk"')
    lLines.append(build_divider())
    lLines.append(f'period = {oOptions.clock_period:.3f}')
    lLines.append('')
    lLines.append('# SCK, generated from device_clk and forwarded to the part.')
    lLines.append('[[clock]]')
    lLines.append('name = "spi_sck"')
    lLines.append('port = "O_SPI_SCK"')
    lLines.append('generator = {source = "q_spi_sck_reg", master_pin = "C", target_pin = "Q", master_clock = "device_clk"}')
    lLines.append(build_divider())
    lLines.append(f'period = {oOptions.sck_period:.3f}')
    lLines.append(f'idle = "{oStandard.idle}"')
    lLines.append('if_signal = "SCK"')
    lLines.append('')
    lLines.append(f'# COPI changes on the {sChange} edge of SCK, and the part samples it on the next {sSample} edge.')
    lLines.extend(build_port('O_SPI_COPI', 'SDR-SS-O', 'COPI', ('device_clk', oEdges.copi_launch, oEdges.copi_launch), ('spi_sck', oEdges.copi_setup_capture, oEdges.copi_hold_capture), 'q_spi_copi_reg'))
    lLines.append('')
    lLines.append(f'# CS is timed to the first and last {sSample} edges of SCK.')
    lLines.extend(build_port('O_SPI_CS', 'SDR-SS-O-FLC', 'CS', ('device_clk', oEdges.cs_setup_launch, oEdges.cs_hold_launch), ('spi_sck', oEdges.copi_setup_capture, oEdges.copi_hold_capture), 'q_spi_cs_reg'))
    lLines.append('')
    lLines.append(f'# The part changes CIPO on the {sChange} edge of SCK, and the device captures it on device_clk at the next {sSample} edge.')
    lLines.extend(build_port('I_SPI_CIPO', 'SDR-SS-RT-DI', 'CIPO', ('spi_sck', oEdges.cipo_launch, oEdges.cipo_launch), ('device_clk', oEdges.cipo_setup_capture, oEdges.cipo_hold_capture), 'q_spi_cipo_reg'))
    return lLines


def build_port(sName, sMethodology, sSignal, tLaunch, tCapture, sRegister):
    lLines = []
    lLines.append('[[port]]')
    lLines.append('status = "analyze"')
    lLines.append(f'name = "{sName}"')
    lLines.append(f'registers = ["{sRegister}"]')
    lLines.append(f'launch_clock = {{name = "{tLaunch[0]}", setup_edge = {tLaunch[1]}, hold_edge = {tLaunch[2]}}}')
    lLines.append(f'capture_clock = {{name = "{tCapture[0]}", setup_edge = "{tCapture[1]}", hold_edge = "{tCapture[2]}"}}')
    lLines.append('timing_reports = [')
    lLines.append(f'    "timing_reports/SPI_INTERFACE_NAME.{sSignal}_timing.rpt",')
    lLines.append(']')
    lLines.append(build_divider())
    lLines.append(f'methodology = "{sMethodology}"')
    lLines.append(f'if_signal = "{sSignal}"')
    return lLines


def build_part(oOptions, oStandard):
    lLines = []
    lLines.append(f'# stacv part file for the peripheral of a {oOptions.wires}-wire SPI interface, SPI mode {oOptions.mode}.')
    lLines.append(f'# Created by:  {build_command(oOptions)}')
    lLines.append('#')
    lLines.append('# Keys are described in:')
    lLines.append(f'# {DOCS_URL}/part.rst')
    lLines.append('#')
    lLines.append('# Fill in each value from the part\'s datasheet, with its symbol and where it comes from.')
    lLines.append(f'# The values are {PLACEHOLDER} until then, which stacv stops on.')
    lLines.append('# Rename the pins to the datasheet\'s.')
    lLines.extend(build_header_divider_lines())
    lLines.append('#')
    lLines.append('# All delays are in nanoseconds.')
    lLines.append('# All frequencies are in MHz.')
    lLines.append('')
    lLines.append('[properties]')
    lLines.append('manufacturer = "MANUFACTURER"')
    lLines.append('part_number = "PART_NUMBER"')
    lLines.append('')
    lLines.append('[datasheet]')
    lLines.append('name = "DATASHEET_NAME"')
    lLines.append('url = "DATASHEET_URL"')
    lLines.append('version = "DATASHEET_VERSION"')
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
    lLines.extend(build_input_pin('COPI', oStandard.sample_edge, 'tSU', 'tH'))
    lLines.append('')
    lLines.extend(build_input_pin('CS', oStandard.sample_edge, 'tCSS', 'tCSH'))
    lLines.append('')
    lLines.append('[[interface.pin]]')
    lLines.append('name = "CIPO"')
    lLines.append(build_placeholder('cko_max', 'tCO'))
    lLines.append(build_placeholder('cko_min', 'tCO'))
    lLines.append(build_clock())
    lLines.append(build_divider())
    lLines.append('methodology = "SDR-SS-RT-DO"')
    lLines.append('if_signal = "CIPO"')
    lLines.append(f'launch_edge = "{oStandard.change_edge}"')
    return lLines


def build_input_pin(sName, sCaptureEdge, sSetupSymbol, sHoldSymbol):
    lLines = []
    lLines.append('[[interface.pin]]')
    lLines.append(f'name = "{sName}"')
    lLines.append(build_placeholder('setup', sSetupSymbol))
    lLines.append(build_placeholder('hold', sHoldSymbol))
    lLines.append(build_clock())
    lLines.append(build_divider())
    lLines.append('methodology = "SDR-SS-I"')
    lLines.append(f'if_signal = "{sName}"')
    lLines.append(f'capture_edge = "{sCaptureEdge}"')
    return lLines


def build_clock():
    # The fastest SCK the part's pin allows is a datasheet value.
    return f'clock = {{if_signal = "SCK", max_frequency = "{PLACEHOLDER}"}}'


def build_placeholder(sKey, sSymbol):
    return f'{sKey} = {{value = "{PLACEHOLDER}", symbol = "{sSymbol}", source = "{PLACEHOLDER}"}}'


def build_traces(oOptions):
    lLines = []
    lLines.append(f'# stacv traces file for a {oOptions.wires}-wire SPI interface, with the device as the {oOptions.type}.')
    lLines.append(f'# Created by:  {build_command(oOptions)}')
    lLines.append('#')
    lLines.append('# Keys are described in:')
    lLines.append(f'# {DOCS_URL}/traces.rst')
    lLines.append('#')
    lLines.append('# Fill in each trace\'s delays from the board, or leave {} to use default_delay.')
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
