'''
Creates the configuration, part and traces files of an RMII or MII interface, with the device as the MAC, linked by the
signals of the standard.

The standard fixes the clocks and every edge, so the user fills in only the names in the design, the PHY's timing
from its datasheet, and the trace delays.
'''

from stacv.create import spi_template
from stacv.mac_phy import protocols
from stacv.part import part
from stacv.standards import standards

DOCS_URL = spi_template.DOCS_URL

# The text of each protocol's files that the standard decides.
TEXT = {}
TEXT['rmii'] = {
    'config_timing': [
        '# RMII:  every signal is launched and captured on the rising edge of the 50 MHz',
        '#        REF_CLK, at the MAC and at the PHY, so there are no edges or periods to',
        '#        set.  Where REF_CLK comes from (the PHY, the MAC or an oscillator) is in',
        '#        the traces file: its delay to each end.',
    ],
    'config_clocks': [
        '# REF_CLK: the 50 MHz reference clock the MAC receives on its port.  stacv creates',
        '# the clock with this name (create_clock); if the board constraints already create',
        '# a clock on the port, Vivado warns of the two, so remove the other.',
    ],
    'config_tx': ['# TXD[1:0], TX_EN and TX_ER: data from the MAC to the PHY.'],
    'config_rx': ['# RXD[1:0], CRS_DV and RX_ER: data from the PHY to the MAC.'],
    'part_reference': [
        '# The RMII specification gives the setup, hold and output delay too; use the part\'s',
        '# datasheet where it gives them.',
    ],
    'part_tx': ['# TXD, TX_EN, TX_ER: setup and hold to the rising edge of REF_CLK at the PHY, such as TSU and THOLD.'],
    'part_rx': ['# RXD, CRS_DV, RX_ER: output delay from the rising edge of REF_CLK at the PHY, such as TDELAY.'],
    'traces_clocks': [
        '# Each trace is linked to its port and pin by signal, so the names are free.',
        '# REF_CLK comes from a source, the PHY, the MAC or an oscillator, on a trace to each',
        '# end: source_to_device to the port it arrives on, source_to_part to the PHY\'s',
        '# REF_CLK pin.  source is any name for the source; the two traces share it.',
    ],
}
TEXT['mii'] = {
    'config_timing': [
        '# MII:   the PHY sends TX_CLK and RX_CLK, 25 MHz at 100 Mbit/s.  The MAC launches TXD',
        '#        on the rising edge of TX_CLK and the PHY samples it on the next; the PHY',
        '#        launches RXD on the rising edge of RX_CLK and the MAC samples it on the next,',
        '#        so there are no edges or periods to set.  At 10 Mbit/s the clocks are 2.5 MHz',
        '#        with the same timing at the pins, so timing at 25 MHz covers both.  CRS and',
        '#        COL are asynchronous and are not timed.',
    ],
    'config_clocks': [
        '# TX_CLK and RX_CLK: the clocks the MAC receives from the PHY on its ports.  stacv',
        '# creates each clock with its name (create_clock); if the board constraints already',
        '# create a clock on the port, Vivado warns of the two, so remove the other.',
    ],
    'config_tx': ['# TXD[3:0], TX_EN and TX_ER: data from the MAC to the PHY, launched on TX_CLK.'],
    'config_rx': ['# RXD[3:0], RX_DV and RX_ER: data from the PHY to the MAC, sent with RX_CLK.'],
    'part_reference': [
        '# IEEE 802.3 Clause 22 gives the setup, hold and output delay too; use the part\'s',
        '# datasheet where it gives them.  A PHY with several modes may give the MII clocks pins',
        '# of their own, such as MII_TXCLK; use the MII pins and timing, not another mode\'s.',
    ],
    'part_tx': ['# TXD, TX_EN, TX_ER: setup and hold to the rising edge of TX_CLK at the PHY, such as tSU and tH.'],
    'part_rx': ['# RXD, RX_DV, RX_ER: output delay from the rising edge of RX_CLK at the PHY, such as tDELAY.'],
    'traces_clocks': [
        '# Each trace is linked to its port and pin by signal, so the names are free.',
        '# The PHY sends TX_CLK and RX_CLK to the MAC, each on a trace of its own.',
    ],
}


def create_files(oProtocol):
    # The three files, by name.
    dFiles = {}
    dFiles[f'{oProtocol.configuration}_config.toml'] = build_config(oProtocol)
    dFiles['part.toml'] = build_part(oProtocol)
    dFiles['traces.toml'] = build_traces(oProtocol)
    return dFiles


def build_command(oProtocol):
    return f'stacv create template {oProtocol.configuration}'


def build_divider(oProtocol):
    return f'#--- set by {build_command(oProtocol)}; do not change below ---'


def design_placeholder(*lNames):
    return spi_template.build_design_placeholder(*lNames)


def datasheet_placeholder(*lNames):
    return spi_template.build_datasheet_placeholder(*lNames)


def collect_signals(oProtocol, bFromMac):
    lSignals = []
    for oSignal in oProtocol.signals:
        if oSignal.is_from_mac() == bFromMac:
            lSignals.append(oSignal)
    return lSignals


def build_config(oProtocol):
    dText = TEXT[oProtocol.configuration]
    sStandard = oProtocol.standard
    lLines = []
    lLines.append(f'# stacv {sStandard} configuration file, with the device as the MAC.')
    lLines.append(f'# Created by:  {build_command(oProtocol)}')
    lLines.append('#')
    lLines.append('# Keys are described in:')
    lLines.append(f'# {DOCS_URL}/{oProtocol.configuration}_config.rst')
    lLines.append('#')
    lLines.append('# stacv generates the interface file, the constraints and the report script')
    lLines.append('# from this file.  Only this file, the part file and the traces file are edited.')
    lLines.append('#')
    lLines.append('# Replace each FROM_DESIGN_... with the name in your design; stacv stops on it until then.')
    lLines.append('# Each placeholder is named after its key, so it can be found and replaced on its own.')
    lLines.append('# Registers are named as Vivado names them:  the hierarchy separated by /, with')
    lLines.append(f'# _reg added, and the bits of a bus as reg[*], such as u_mac/{oProtocol.configuration}_txd_reg[*].')
    lLines.append(f'# A bus port is written NAME[upper:lower], such as O_{sStandard}_{collect_signals(oProtocol, True)[0].part_pin}.')
    lLines.append('#')
    lLines.extend(dText['config_timing'])
    lLines.append('#')
    lLines.append('# Paths are relative to this file.')
    lLines.append('')
    lLines.append(f'interface = "{oProtocol.configuration}"')
    lLines.append(f'name      = "{sStandard}"')
    lLines.append(f'role      = "{standards.MAC}"')
    lLines.append('')
    lLines.append('part    = "part.toml"')
    lLines.append('traces  = "traces.toml"')
    lLines.append('')
    lLines.append('timing_reports_dir = "timing_reports"')
    lLines.append('')
    lLines.extend(dText['config_clocks'])
    for oClock in oProtocol.clocks:
        lLines.append(f'[{oClock.table}]')
        lLines.append(f'name = "{design_placeholder(oClock.table, "name")}"')
        lLines.append(f'port = "{design_placeholder(oClock.table, "port")}"')
        lLines.append('')
    lLines.extend(dText['config_tx'])
    lLines.append(f'# TX_ER and RX_ER are optional in {sStandard}: if the design does not use one, remove its')
    lLines.append('# table here and its trace in the traces file.')
    for oSignal in collect_signals(oProtocol, True):
        lLines.extend(build_signal_table(oSignal.table))
    lLines.append('')
    lLines.extend(dText['config_rx'])
    for oSignal in collect_signals(oProtocol, False):
        lLines.extend(build_signal_table(oSignal.table))
    return lLines


def build_signal_table(sTable):
    lLines = []
    lLines.append(f'[{sTable}]')
    lLines.append(f'port     = "{design_placeholder(sTable, "port")}"')
    lLines.append(f'register = "{design_placeholder(sTable, "register")}"')
    lLines.append('')
    return lLines


def build_part(oProtocol):
    dText = TEXT[oProtocol.configuration]
    sDivider = build_divider(oProtocol)
    lLines = []
    lLines.append(f'# stacv part file for the PHY of an {oProtocol.standard} interface.')
    lLines.append(f'# Created by:  {build_command(oProtocol)}')
    lLines.append('#')
    lLines.append('# Keys are described in:')
    lLines.append(f'# {DOCS_URL}/part.rst')
    lLines.append('#')
    lLines.append('# Fill in each value from the part\'s datasheet, with its symbol and where it comes from,')
    lLines.append('# such as source = "DS60001648 Table 7-22, page 70": the document, its table or section and page.')
    lLines.append(f'# The values are {part.PLACEHOLDER}_... until then, each named after its key, which stacv stops on.')
    lLines.append('# Rename the pins to the datasheet\'s; the traces file keeps its trace names, as the')
    lLines.append('# files are linked by signal, not by name.  Remove the pin of an optional signal')
    lLines.append('# (TX_ER, RX_ER) that the design does not use, or leave it: an unused one needs no port.')
    lLines.extend(dText['part_reference'])
    lLines.append(f'# Keys below each "set by {build_command(oProtocol)}" line are set by the {oProtocol.standard} standard;')
    lLines.append('# do not change them.')
    lLines.append('#')
    lLines.append('# All delays are in nanoseconds.')
    lLines.append('# All frequencies are in MHz.')
    lLines.append('')
    lLines.append('[properties]')
    lLines.append(f'manufacturer = "{datasheet_placeholder("manufacturer")}"')
    lLines.append(f'part_number = "{datasheet_placeholder("part_number")}"')
    lLines.append('')
    lLines.append('[datasheet]')
    lLines.append(f'name = "{datasheet_placeholder("datasheet", "name")}"')
    lLines.append(f'url = "{datasheet_placeholder("datasheet", "url")}"')
    lLines.append(f'version = "{datasheet_placeholder("datasheet", "version")}"')
    lLines.append('')
    lLines.append('[[interface]]')
    lLines.append(f'name = "{oProtocol.standard}"')
    lLines.append(sDivider)
    lLines.append(f'if_standard = "{oProtocol.standard}"')
    lLines.append(f'if_role = "{standards.PHY}"')
    lLines.append('')
    for oClock in oProtocol.clocks:
        lLines.append('[[interface.clock_pin]]')
        lLines.append(f'name = "{oClock.signal}"')
        lLines.append(sDivider)
        lLines.append(f'if_signal = "{oClock.signal}"')
        lLines.append('')
    lLines.extend(dText['part_tx'])
    for oSignal in collect_signals(oProtocol, True):
        lLines.extend(build_input_pin(oProtocol, oSignal))
    lLines.extend(dText['part_rx'])
    lLines.append('# If the datasheet gives only a maximum, give 0 as the minimum, the pessimistic value.')
    for oSignal in collect_signals(oProtocol, False):
        lLines.extend(build_output_pin(oProtocol, oSignal))
    return lLines


def find_clock_signal(oProtocol, oSignal):
    for oClock in oProtocol.clocks:
        if oClock.table == oSignal.clock_table:
            return oClock.signal
    return None


def build_input_pin(oProtocol, oSignal):
    lLines = []
    lLines.append('[[interface.pin]]')
    lLines.append(f'name = "{oSignal.part_pin}"')
    lLines.append(build_constraint(oSignal.signal, 'setup'))
    lLines.append(build_constraint(oSignal.signal, 'hold'))
    lLines.append(build_clock(oSignal.signal, find_clock_signal(oProtocol, oSignal)))
    lLines.append(build_divider(oProtocol))
    lLines.append(f'methodology = "{oSignal.part_methodology}"')
    lLines.append(f'if_signal = "{oSignal.signal}"')
    lLines.append('capture_edge = "Rising"')
    lLines.append('')
    return lLines


def build_output_pin(oProtocol, oSignal):
    lLines = []
    lLines.append('[[interface.pin]]')
    lLines.append(f'name = "{oSignal.part_pin}"')
    lLines.append(build_constraint(oSignal.signal, 'cko_max'))
    lLines.append(build_constraint(oSignal.signal, 'cko_min'))
    lLines.append(build_clock(oSignal.signal, find_clock_signal(oProtocol, oSignal)))
    lLines.append(build_divider(oProtocol))
    lLines.append(f'methodology = "{oSignal.part_methodology}"')
    lLines.append(f'if_signal = "{oSignal.signal}"')
    lLines.append('launch_edge = "Rising"')
    lLines.append('')
    return lLines


def build_constraint(sSignal, sKey):
    sValue = datasheet_placeholder(sSignal, sKey, 'value')
    sSymbol = datasheet_placeholder(sSignal, sKey, 'symbol')
    sSource = datasheet_placeholder(sSignal, sKey, 'source')
    return f'{sKey} = {{value = "{sValue}", symbol = "{sSymbol}", source = "{sSource}"}}'


def build_clock(sSignal, sClockSignal):
    # The standard fixes the clock's frequency; the part's datasheet gives the limit.
    return f'clock = {{if_signal = "{sClockSignal}", max_frequency = "{datasheet_placeholder(sSignal, "max_frequency")}"}}'


def build_traces(oProtocol):
    dText = TEXT[oProtocol.configuration]
    lLines = []
    lLines.append(f'# stacv traces file for an {oProtocol.standard} interface, with the device as the MAC.')
    lLines.append(f'# Created by:  {build_command(oProtocol)}')
    lLines.append('#')
    lLines.append('# Keys are described in:')
    lLines.append(f'# {DOCS_URL}/traces.rst')
    lLines.append('#')
    lLines.append('# Fill in each trace\'s delays from the board, or leave {} to use default_delay.')
    lLines.extend(dText['traces_clocks'])
    lLines.append(f'# Keys below each "set by {build_command(oProtocol)}" line are set by the {oProtocol.standard} standard;')
    lLines.append('# do not change them.')
    lLines.append('#')
    lLines.append('# Delays are in nanoseconds.')
    lLines.append('')
    lLines.append('default_delay = {max_delay = 1.00, min_delay = 0.00}')
    for oClock in oProtocol.clocks:
        lLines.extend(build_clock_traces(oProtocol, oClock))
    for oSignal in collect_signals(oProtocol, True):
        lLines.extend(build_data_trace(oProtocol, oSignal.table, oSignal.signal, 'device_to_part'))
    for oSignal in collect_signals(oProtocol, False):
        lLines.extend(build_data_trace(oProtocol, oSignal.table, oSignal.signal, 'part_to_device'))
    return lLines


def build_clock_traces(oProtocol, oClock):
    # A clock from a source reaches each end on a trace of its own; a clock the PHY sends is one trace to the MAC.
    if not oClock.from_source:
        return build_data_trace(oProtocol, oClock.table, oClock.signal, 'part_to_device')
    sSource = f'{oClock.table}_source'
    lLines = ['']
    lLines.extend(build_source_trace(oProtocol, oClock, f'{oClock.table}_to_device', sSource, 'source_to_device'))
    lLines.append('')
    lLines.extend(build_source_trace(oProtocol, oClock, f'{oClock.table}_to_part', sSource, 'source_to_part'))
    return lLines


def build_source_trace(oProtocol, oClock, sName, sSource, sDelay):
    lLines = []
    lLines.append('[[trace]]')
    lLines.append(f'name = "{sName}"')
    lLines.append(f'source = "{sSource}"')
    lLines.append(f'{sDelay} = {{}}')
    lLines.append(build_divider(oProtocol))
    lLines.append(f'if_signal = "{oClock.signal}"')
    return lLines


def build_data_trace(oProtocol, sTable, sSignal, sDirection):
    lLines = ['']
    lLines.append('[[trace]]')
    lLines.append(f'name = "{sTable}"')
    lLines.append(f'{sDirection} = {{}}')
    lLines.append(build_divider(oProtocol))
    lLines.append(f'if_signal = "{sSignal}"')
    return lLines


def get_protocol(sFileType):
    return protocols.get_protocol(sFileType)
