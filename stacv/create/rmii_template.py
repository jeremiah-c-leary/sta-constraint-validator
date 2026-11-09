'''
Creates the RMII configuration, part and traces files of an RMII interface, with the device as the MAC, linked by the
signals of the RMII standard.

RMII fixes the clock at 50 MHz and every edge, so the user fills in only the names in the design, the PHY's timing
from its datasheet, and the trace delays, with the delays of REF_CLK from its source to each end.
'''

from stacv.create import spi_template
from stacv.part import part
from stacv.standards import standards

FILE_NAMES = ['rmii_config.toml', 'part.toml', 'traces.toml']
DOCS_URL = spi_template.DOCS_URL
DIVIDER = '#--- set by stacv create template rmii; do not change below ---'
# Each signal's table in the configuration, its part pin, and whether it is optional.
TX_SIGNALS = [('txd', 'TXD', 'TXD[1:0]', False), ('tx_en', 'TX_EN', 'TX_EN', False), ('tx_er', 'TX_ER', 'TX_ER', True)]
RX_SIGNALS = [('rxd', 'RXD', 'RXD[1:0]', False), ('crs_dv', 'CRS_DV', 'CRS_DV', False), ('rx_er', 'RX_ER', 'RX_ER', True)]
COMMAND = 'stacv create template rmii'


def create_files():
    # The three files, by name.
    dFiles = {}
    dFiles['rmii_config.toml'] = build_rmii_config()
    dFiles['part.toml'] = build_part()
    dFiles['traces.toml'] = build_traces()
    return dFiles


def design_placeholder(*lNames):
    return spi_template.build_design_placeholder(*lNames)


def datasheet_placeholder(*lNames):
    return spi_template.build_datasheet_placeholder(*lNames)


def build_rmii_config():
    lLines = []
    lLines.append('# stacv RMII configuration file, with the device as the MAC.')
    lLines.append(f'# Created by:  {COMMAND}')
    lLines.append('#')
    lLines.append('# Keys are described in:')
    lLines.append(f'# {DOCS_URL}/rmii_config.rst')
    lLines.append('#')
    lLines.append('# stacv generates the interface file, the constraints and the report script')
    lLines.append('# from this file.  Only this file, the part file and the traces file are edited.')
    lLines.append('#')
    lLines.append('# Replace each FROM_DESIGN_... with the name in your design; stacv stops on it until then.')
    lLines.append('# Each placeholder is named after its key, so it can be found and replaced on its own.')
    lLines.append('# Registers are named as Vivado names them:  the hierarchy separated by /, with')
    lLines.append('# _reg added, and the bits of a bus as reg[*], such as u_mac/rmii_txd_reg[*].')
    lLines.append('# A bus port is written NAME[upper:lower], such as O_RMII_TXD[1:0].')
    lLines.append('#')
    lLines.append('# RMII:  every signal is launched and captured on the rising edge of the 50 MHz')
    lLines.append('#        REF_CLK, at the MAC and at the PHY, so there are no edges or periods to')
    lLines.append('#        set.  Where REF_CLK comes from (the PHY, the MAC or an oscillator) is in')
    lLines.append('#        the traces file: its delay to each end.')
    lLines.append('#')
    lLines.append('# Paths are relative to this file.')
    lLines.append('')
    lLines.append('interface = "rmii"')
    lLines.append('name      = "RMII"')
    lLines.append(f'role      = "{standards.MAC}"')
    lLines.append('')
    lLines.append('part    = "part.toml"')
    lLines.append('traces  = "traces.toml"')
    lLines.append('')
    lLines.append('timing_reports_dir = "timing_reports"')
    lLines.append('')
    lLines.append('# REF_CLK: the 50 MHz reference clock the MAC receives on its port.  stacv creates')
    lLines.append('# the clock with this name (create_clock); if the board constraints already create')
    lLines.append('# a clock on the port, Vivado warns of the two, so remove the other.')
    lLines.append('[ref_clk]')
    lLines.append(f'name = "{design_placeholder("ref_clk", "name")}"')
    lLines.append(f'port = "{design_placeholder("ref_clk", "port")}"')
    lLines.append('')
    lLines.append('# TXD[1:0], TX_EN and TX_ER: data from the MAC to the PHY.')
    lLines.append('# TX_ER and RX_ER are optional in RMII: if the design does not use one, remove its')
    lLines.append('# table here and its trace in the traces file.')
    for sTable, sSignal, sPin, bOptional in TX_SIGNALS:
        lLines.extend(build_signal_table(sTable))
    lLines.append('')
    lLines.append('# RXD[1:0], CRS_DV and RX_ER: data from the PHY to the MAC.')
    for sTable, sSignal, sPin, bOptional in RX_SIGNALS:
        lLines.extend(build_signal_table(sTable))
    return lLines


def build_signal_table(sTable):
    lLines = []
    lLines.append(f'[{sTable}]')
    lLines.append(f'port     = "{design_placeholder(sTable, "port")}"')
    lLines.append(f'register = "{design_placeholder(sTable, "register")}"')
    lLines.append('')
    return lLines


def build_part():
    lLines = []
    lLines.append('# stacv part file for the PHY of an RMII interface.')
    lLines.append(f'# Created by:  {COMMAND}')
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
    lLines.append('# The RMII specification gives the setup, hold and output delay too; use the part\'s')
    lLines.append('# datasheet where it gives them.')
    lLines.append('# Keys below each "set by stacv create template rmii" line are set by the RMII standard;')
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
    lLines.append('name = "RMII"')
    lLines.append(DIVIDER)
    lLines.append('if_standard = "RMII"')
    lLines.append(f'if_role = "{standards.PHY}"')
    lLines.append('')
    lLines.append('[[interface.clock_pin]]')
    lLines.append('name = "REF_CLK"')
    lLines.append(DIVIDER)
    lLines.append('if_signal = "REF_CLK"')
    lLines.append('')
    lLines.append('# TXD, TX_EN, TX_ER: setup and hold to the rising edge of REF_CLK at the PHY, such as TSU and THOLD.')
    for sTable, sSignal, sPin, bOptional in TX_SIGNALS:
        lLines.extend(build_input_pin(sPin, sSignal))
    lLines.append('# RXD, CRS_DV, RX_ER: output delay from the rising edge of REF_CLK at the PHY, such as TDELAY.')
    lLines.append('# If the datasheet gives only a maximum, give 0 as the minimum, the pessimistic value.')
    for sTable, sSignal, sPin, bOptional in RX_SIGNALS:
        lLines.extend(build_output_pin(sPin, sSignal))
    return lLines


def build_input_pin(sPin, sSignal):
    lLines = []
    lLines.append('[[interface.pin]]')
    lLines.append(f'name = "{sPin}"')
    lLines.append(build_constraint(sSignal, 'setup'))
    lLines.append(build_constraint(sSignal, 'hold'))
    lLines.append(build_clock(sSignal))
    lLines.append(DIVIDER)
    lLines.append('methodology = "SDR-SYS-I"')
    lLines.append(f'if_signal = "{sSignal}"')
    lLines.append('capture_edge = "Rising"')
    lLines.append('')
    return lLines


def build_output_pin(sPin, sSignal):
    lLines = []
    lLines.append('[[interface.pin]]')
    lLines.append(f'name = "{sPin}"')
    lLines.append(build_constraint(sSignal, 'cko_max'))
    lLines.append(build_constraint(sSignal, 'cko_min'))
    lLines.append(build_clock(sSignal))
    lLines.append(DIVIDER)
    lLines.append('methodology = "SDR-SYS-O"')
    lLines.append(f'if_signal = "{sSignal}"')
    lLines.append('launch_edge = "Rising"')
    lLines.append('')
    return lLines


def build_constraint(sSignal, sKey):
    sValue = datasheet_placeholder(sSignal, sKey, 'value')
    sSymbol = datasheet_placeholder(sSignal, sKey, 'symbol')
    sSource = datasheet_placeholder(sSignal, sKey, 'source')
    return f'{sKey} = {{value = "{sValue}", symbol = "{sSymbol}", source = "{sSource}"}}'


def build_clock(sSignal):
    # RMII's clock is 50 MHz; the part's datasheet gives the limit.
    return f'clock = {{if_signal = "REF_CLK", max_frequency = "{datasheet_placeholder(sSignal, "max_frequency")}"}}'


def build_traces():
    lLines = []
    lLines.append('# stacv traces file for an RMII interface, with the device as the MAC.')
    lLines.append(f'# Created by:  {COMMAND}')
    lLines.append('#')
    lLines.append('# Keys are described in:')
    lLines.append(f'# {DOCS_URL}/traces.rst')
    lLines.append('#')
    lLines.append('# Fill in each trace\'s delays from the board, or leave {} to use default_delay.')
    lLines.append('# The data traces are linked to their port and pin by signal, so keep their names.')
    lLines.append('# REF_CLK comes from a source, the PHY, the MAC or an oscillator, on a trace to each')
    lLines.append('# end, which names its pin: the port REF_CLK arrives on, and the PHY\'s REF_CLK pin.')
    lLines.append('# source is any name for the source; the two traces share it.')
    lLines.append('# Keys below each "set by stacv create template rmii" line are set by the RMII standard;')
    lLines.append('# do not change them.')
    lLines.append('#')
    lLines.append('# Delays are in nanoseconds.')
    lLines.append('')
    lLines.append('default_delay = {max_delay = 1.00, min_delay = 0.00}')
    lLines.append('')
    lLines.append('[[trace]]')
    lLines.append('name = "ref_clk_to_device"')
    lLines.append('source = "ref_clk_source"')
    lLines.append(f'device_pin = "{design_placeholder("ref_clk", "port")}"')
    lLines.append('source_to_device = {}')
    lLines.append('')
    lLines.append('[[trace]]')
    lLines.append('name = "ref_clk_to_part"')
    lLines.append('source = "ref_clk_source"')
    lLines.append('part_pin = "REF_CLK"')
    lLines.append('source_to_part = {}')
    for sTable, sSignal, sPin, bOptional in TX_SIGNALS:
        lLines.extend(build_data_trace(sTable, sSignal, 'device_to_part'))
    for sTable, sSignal, sPin, bOptional in RX_SIGNALS:
        lLines.extend(build_data_trace(sTable, sSignal, 'part_to_device'))
    return lLines


def build_data_trace(sTable, sSignal, sDirection):
    lLines = ['']
    lLines.append('[[trace]]')
    lLines.append(f'name = "{sTable}"')
    lLines.append(f'{sDirection} = {{}}')
    lLines.append(DIVIDER)
    lLines.append(f'if_signal = "{sSignal}"')
    return lLines
