'''
Draws the device, the part and the traces between them as text, with the registers that drive and capture each port
and the clocks of those registers.

    -----------------------------------------------------------+                       +------------
      Device                                                   |                       |  DAC81404
                                                               |                       |
      clk_100mhz --+--> [q_spi_output_data_reg] ---> O_DAC_DATA   [X] --- data_output --> [X] SDIN
                   |                                               |                       |
                   +--> [q_spi_input_data_reg] <---- I_DAC_DATA   [X] <-- data_input ---- [X] SDO
                   |                                               |                       |
                   +--> [q_spi_output_clock_reg] --> O_DAC_SCLK   [X] --- clock --------> [X] SCLK

Each clock that clocks a register roots a tree: the launch clock of an output, the capture clock of an input, and the
master clock of a clock the device generates.  A clock that enters on a port roots its tree on that port's row, and a
clock from a source comes in from the top edge, between the device and the part, to both.  A port with several
registers joins them; only a register's own end has an arrow.  A port with no registers, such as a deferred port, is
drawn after the trees.
'''

from stacv.interface import port
from stacv.methodology import methodology
from stacv.visualize import text_row

DEVICE_NAME = 'Device'
INDENT = '  '
MARGIN = 2
ARROW_LENGTH_AROUND_NAME = 8
SENDS = 'sends'
RECEIVES = 'receives'
REGISTERS = 'registers'
CLOCK_IN = 'clock in'
PLAIN = 'plain'


class DiagramRow():
    '''
    One trace, with the port at its device end and what the device connects to that port.
    '''

    def __init__(self, sKind, oTrace):
        self.kind = sKind
        self.trace = oTrace
        self.port = get_device_end(oTrace)
        # The clock of the registers, or the clock that enters on the port; None for a row with neither.
        self.clock = None
        # Each register and whether it sends to the port or receives from it.
        self.registers = []
        # The trace from a clock source to the part, drawn on the row of the source's trace to the device.
        self.source_part_trace = None


class Layout():
    '''
    The columns of the diagram.
    '''

    def __init__(self):
        self.trunk = None
        self.join = None
        self.port = None
        self.device_edge = None
        self.part_edge = None
        self.longest_trace_name = None
        self.arrow_stretch = 0
        self.part_width = None


def draw_block_diagram(oInterface, oTraceList, oPart):
    lRows = build_rows(oInterface, select_traces(oInterface, oTraceList))
    lTrees = group_rows_into_trees(lRows)
    lPlainRows = find_rows_without_clock(lRows)
    oLayout = calculate_layout(lRows, lTrees, oPart)
    lLines = []
    lLines.append(draw_border(oLayout.device_edge, oLayout.part_edge, oLayout.part_width))
    lLines.append(draw_label_row(oPart.part_number, oLayout.device_edge, oLayout.part_edge))
    lLines.append(draw_blank_row(oLayout))
    for sClock, lTreeRows in lTrees:
        lLines.extend(draw_tree(sClock, lTreeRows, oLayout))
        lLines.append(draw_blank_row(oLayout))
    for oRow in lPlainRows:
        lLines.append(draw_plain_row(oRow, oLayout))
        lLines.append(draw_blank_row(oLayout))
    lLines.append(draw_border(oLayout.device_edge, oLayout.part_edge, oLayout.part_width))
    draw_sources(lLines, lRows, oLayout)
    return lLines


def find_clock_ports(oInterface):
    # Each forwarded clock's port gets one row, in the order the ports first use it.
    lClockPorts = []
    for oPort in oInterface.get_analyzed_ports():
        if oPort.forwarded_clock.port not in lClockPorts:
            lClockPorts.append(oPort.forwarded_clock.port)
    return lClockPorts


def select_traces(oInterface, oTraceList):
    lTraces = []
    for oPort in oInterface.ports:
        add_traces(lTraces, find_traces_from_device_pin(oTraceList.traces, oPort.name))
    for sClockPort in find_clock_ports(oInterface):
        add_traces(lTraces, find_traces_from_device_pin(oTraceList.traces, sClockPort))
    # A clock source drives the part too, on a trace of its own.
    for oTrace in list(lTraces):
        if oTrace.source is not None:
            add_traces(lTraces, find_traces_from_source_to_part(oTraceList.traces, oTrace.source))
    return lTraces


def add_traces(lTraces, lNewTraces):
    # A bidirectional port has a [[port]] table for each direction, but its trace is drawn once.
    for oTrace in lNewTraces:
        if oTrace not in lTraces:
            lTraces.append(oTrace)


def find_traces_from_source_to_part(lTraces, sSource):
    lMatchingTraces = []
    for oTrace in lTraces:
        if oTrace.source == sSource and oTrace.source_to_part is not None:
            lMatchingTraces.append(oTrace)
    return lMatchingTraces


def find_traces_from_device_pin(lTraces, sDevicePin):
    lMatchingTraces = []
    for oTrace in lTraces:
        if oTrace.device_pin == sDevicePin:
            lMatchingTraces.append(oTrace)
    return lMatchingTraces


def build_rows(oInterface, lTraces):
    lRows = []
    for oTrace in lTraces:
        lRows.append(build_row(oInterface, oTrace))
    return attach_source_traces(lRows)


def build_row(oInterface, oTrace):
    lPorts = find_analyzed_ports_named(oInterface, oTrace.device_pin)
    if len(lPorts) > 0:
        return build_port_row(oTrace, lPorts)
    oClock = find_clock_on_port(oInterface, oTrace.device_pin)
    if oClock is None:
        return DiagramRow(PLAIN, oTrace)
    if oClock.generator is None and not is_input_trace(oTrace):
        # A clock that leaves the device without a generator has no element to draw.
        return DiagramRow(PLAIN, oTrace)
    if oClock.generator is not None:
        oRow = DiagramRow(REGISTERS, oTrace)
        oRow.clock = oClock.generator.master_clock
        oRow.registers.append((oClock.generator.source, SENDS))
        return oRow
    oRow = DiagramRow(CLOCK_IN, oTrace)
    oRow.clock = oClock.name
    return oRow


def find_analyzed_ports_named(oInterface, sName):
    lPorts = []
    for oPort in oInterface.ports:
        if oPort.name == sName and oPort.status == port.ANALYZE:
            lPorts.append(oPort)
    return lPorts


def find_clock_on_port(oInterface, sPortName):
    for oClock in oInterface.clocks:
        if oClock.port is not None and oClock.port == sPortName:
            return oClock
    return None


def build_port_row(oTrace, lPorts):
    # A bidirectional port has a table for each direction; it is drawn in the tree of its first table's clock.
    oRow = DiagramRow(REGISTERS, oTrace)
    for oPort in lPorts:
        sClock, sDirection = find_register_clock(oPort)
        if oRow.clock is None:
            oRow.clock = sClock
        for sRegister in oPort.registers:
            oRow.registers.append((sRegister, sDirection))
    return oRow


def find_register_clock(oPort):
    # An output's registers launch on its launch clock; an input's capture on its capture clock.
    if oPort.data_direction == methodology.OUTPUT:
        return oPort.launch_clock.name, SENDS
    return oPort.capture_clock.name, RECEIVES


def attach_source_traces(lRows):
    # A clock source's trace to the part is drawn on the row of its trace to the device, when there is one.
    lKeptRows = []
    for oRow in lRows:
        if is_source_to_part_trace(oRow.trace) and attach_to_clock_row(lRows, oRow.trace):
            continue
        lKeptRows.append(oRow)
    return lKeptRows


def is_source_to_part_trace(oTrace):
    return oTrace.source is not None and oTrace.device_pin is None


def attach_to_clock_row(lRows, oTrace):
    for oRow in lRows:
        if oRow.kind == CLOCK_IN and oRow.trace.source == oTrace.source:
            oRow.source_part_trace = oTrace
            return True
    return False


def group_rows_into_trees(lRows):
    # A tree for each clock, in the order the clocks first appear; a clock that enters on a port leads its tree.
    # A tree whose clock comes from a source is drawn first, so the source comes in from the top edge.
    lTrees = []
    for sClock in find_clocks(lRows):
        lTreeRows = find_rows(lRows, sClock, CLOCK_IN)
        lTreeRows.extend(find_rows(lRows, sClock, REGISTERS))
        lTrees.append((sClock, lTreeRows))
    return move_source_trees_first(lTrees)


def find_clocks(lRows):
    lClocks = []
    for oRow in lRows:
        if oRow.clock is not None and oRow.clock not in lClocks:
            lClocks.append(oRow.clock)
    return lClocks


def find_rows(lRows, sClock, sKind):
    lMatchingRows = []
    for oRow in lRows:
        if oRow.clock == sClock and oRow.kind == sKind:
            lMatchingRows.append(oRow)
    return lMatchingRows


def move_source_trees_first(lTrees):
    lFirst = []
    lRest = []
    for tTree in lTrees:
        if tree_has_source(tTree[1]):
            lFirst.append(tTree)
        else:
            lRest.append(tTree)
    return lFirst + lRest


def tree_has_source(lTreeRows):
    for oRow in lTreeRows:
        if oRow.source_part_trace is not None:
            return True
    return False


def find_rows_without_clock(lRows):
    lPlainRows = []
    for oRow in lRows:
        if oRow.clock is None:
            lPlainRows.append(oRow)
    return lPlainRows


def calculate_layout(lRows, lTrees, oPart):
    oLayout = Layout()
    iClockWidth = find_longest(find_clocks(lRows))
    oLayout.trunk = len(INDENT) + iClockWidth + 3
    iRegisterWidth = find_longest_register(lRows)
    oLayout.join = oLayout.trunk + 5 + iRegisterWidth + 3
    oLayout.port = calculate_port_column(lRows, lTrees, oLayout, iRegisterWidth)
    oLayout.device_edge = calculate_device_edge(lRows, oLayout.port)
    lTraces = collect_traces(lRows)
    oLayout.longest_trace_name = find_longest_trace_name(lTraces)
    iTraceEdge = calculate_part_edge(oLayout.device_edge, oLayout.longest_trace_name)
    oLayout.part_edge = max(iTraceEdge, calculate_source_part_edge(lRows, oLayout.device_edge))
    oLayout.arrow_stretch = oLayout.part_edge - iTraceEdge
    oLayout.part_width = calculate_part_width(oPart.part_number, lTraces)
    return oLayout


def find_longest_register(lRows):
    iLongest = 0
    for oRow in lRows:
        for sRegister, sDirection in oRow.registers:
            iLongest = max(iLongest, len(sRegister) + 2)
    return iLongest


def calculate_port_column(lRows, lTrees, oLayout, iRegisterWidth):
    # The port names line up after the registers, and after the joins when a port has several registers.
    if len(lTrees) == 0:
        return len(INDENT)
    if has_joined_registers(lRows):
        return oLayout.join + 6
    return oLayout.trunk + 5 + iRegisterWidth + 5


def has_joined_registers(lRows):
    for oRow in lRows:
        if len(oRow.registers) > 1:
            return True
    return False


def calculate_device_edge(lRows, iPortColumn):
    iEdge = len(INDENT) + len(DEVICE_NAME) + MARGIN
    for oRow in lRows:
        iEdge = max(iEdge, iPortColumn + len(oRow.port) + MARGIN)
    return iEdge


def collect_traces(lRows):
    lTraces = []
    for oRow in lRows:
        lTraces.append(oRow.trace)
        if oRow.source_part_trace is not None:
            lTraces.append(oRow.source_part_trace)
    return lTraces


def calculate_source_part_edge(lRows, iDeviceEdge):
    # A source's row runs both of its traces through the gap: [X] <-- to device ---+--- to part --> [X]
    iEdge = 0
    for oRow in lRows:
        if oRow.source_part_trace is not None:
            sTraces = '<-- ' + oRow.trace.name + ' ---+--- ' + oRow.source_part_trace.name + ' --> '
            iEdge = max(iEdge, iDeviceEdge + 2 + len(sTraces) + 2)
    return iEdge


def is_input_trace(oTrace):
    return oTrace.device_to_part is None and oTrace.source_to_part is None


def get_device_end(oTrace):
    # A trace from a clock source to the part shows the source where the device pin would be.
    if oTrace.device_pin is None:
        return '(' + oTrace.source + ')'
    return oTrace.device_pin


def get_part_end(oTrace):
    if oTrace.part_pin is None:
        return '(' + oTrace.source + ')'
    return oTrace.part_pin


def is_bidirectional_trace(oTrace):
    return oTrace.device_to_part is not None and oTrace.part_to_device is not None


def find_longest_trace_name(lTraces):
    lNames = []
    for oTrace in lTraces:
        lNames.append(oTrace.name)
    return find_longest(lNames)


def calculate_part_edge(iDeviceEdge, iLongestTraceName):
    # Each edge is followed or preceded by the rest of its [X] and a space:
    # two columns after the device edge and three before the part edge.
    iArrowLength = iLongestTraceName + ARROW_LENGTH_AROUND_NAME
    return iDeviceEdge + 2 + iArrowLength + 3


def calculate_part_width(sPartNumber, lTraces):
    lNames = [sPartNumber]
    for oTrace in lTraces:
        lNames.append(get_part_end(oTrace))
    return MARGIN + find_longest(lNames) + MARGIN


def find_longest(lNames):
    iLongest = 0
    for sName in lNames:
        iLongest = max(iLongest, len(sName))
    return iLongest


def draw_border(iDeviceEdge, iPartEdge, iPartWidth):
    oRow = text_row.TextRow()
    oRow.write(0, '-' * iDeviceEdge + '+')
    oRow.write(iPartEdge, '+' + '-' * iPartWidth)
    return oRow.to_string()


def draw_blank_row(oLayout, lMarks=None):
    # The device and part edges, with any vertical lines of the trees: (column, character).
    oRow = text_row.TextRow()
    if lMarks is not None:
        for iColumn, sCharacter in lMarks:
            oRow.write(iColumn, sCharacter)
    oRow.write(oLayout.device_edge, '|')
    oRow.write(oLayout.part_edge, '|')
    return oRow.to_string()


def draw_label_row(sPartNumber, iDeviceEdge, iPartEdge):
    oRow = text_row.TextRow()
    oRow.write(len(INDENT), DEVICE_NAME)
    oRow.write(iDeviceEdge, '|')
    oRow.write(iPartEdge, '|' + INDENT + sPartNumber)
    return oRow.to_string()


def draw_tree(sClock, lTreeRows, oLayout):
    lLines = []
    for iRow, oRow in enumerate(lTreeRows):
        bFirstRow = iRow == 0
        bLastRow = iRow == len(lTreeRows) - 1
        if oRow.kind == CLOCK_IN:
            lLines.append(draw_clock_in_row(sClock, oRow, oLayout))
            if not bLastRow:
                lLines.append(draw_blank_row(oLayout, [(oLayout.trunk, '|')]))
        else:
            lLines.extend(draw_register_rows(sClock, oRow, bFirstRow, bLastRow, oLayout))
    return lLines


def draw_clock_in_row(sClock, oRow, oLayout):
    # The clock comes out of its port, to the left, and its tree hangs from the +.
    oText = text_row.TextRow()
    oText.write(len(INDENT), sClock + ' <' + '-' * (oLayout.trunk - len(INDENT) - len(sClock) - 2) + '+')
    oText.write(oLayout.trunk + 1, '-' * (oLayout.port - oLayout.trunk - 2) + ' ' + oRow.port)
    return draw_trace_end(oText, oRow, oLayout)


def draw_register_rows(sClock, oRow, bFirstRow, bLastRow, oLayout):
    lLines = []
    for iRegister, tRegister in enumerate(oRow.registers):
        oText = text_row.TextRow()
        draw_trunk_branch(oText, sClock, bFirstRow and iRegister == 0, oLayout)
        draw_register(oText, tRegister, oRow, iRegister, oLayout)
        if iRegister == 0:
            lLines.append(draw_trace_end(oText, oRow, oLayout))
        else:
            lLines.append(draw_blank_row_over(oText, oLayout))
        bMoreRegisters = iRegister < len(oRow.registers) - 1
        if bMoreRegisters or not bLastRow:
            lLines.append(draw_connector_row(bMoreRegisters, not bLastRow or bMoreRegisters, oLayout))
    return lLines


def draw_trunk_branch(oText, sClock, bFirst, oLayout):
    # The first row of a device clock's tree names the clock; every other row branches from the trunk.
    if bFirst:
        oText.write(len(INDENT), sClock + ' ' + '-' * (oLayout.trunk - len(INDENT) - len(sClock) - 1) + '+--> ')
    else:
        oText.write(oLayout.trunk, '+--> ')


def draw_register(oText, tRegister, oRow, iRegister, oLayout):
    sRegister, sDirection = tRegister
    iStart = oLayout.trunk + 5
    sBox = '[' + sRegister + '] '
    oText.write(iStart, sBox)
    iLinkStart = iStart + len(sBox)
    if len(oRow.registers) == 1:
        oText.write(iLinkStart, draw_link(sDirection, oLayout.port - iLinkStart - 1) + ' ' + oRow.port)
        return
    # Several registers join; only a register's own end has an arrow.
    oText.write(iLinkStart, draw_join_link(sDirection, oLayout.join - iLinkStart) + '+')
    if iRegister == 0:
        oText.write(oLayout.join + 1, draw_join_to_port(oRow) + ' ' + oRow.port)


def draw_link(sDirection, iLength):
    if sDirection == SENDS:
        return '-' * (iLength - 1) + '>'
    return '<' + '-' * (iLength - 1)


def draw_join_link(sDirection, iLength):
    if sDirection == SENDS:
        return '-' * iLength
    return '<' + '-' * (iLength - 1)


def draw_join_to_port(oRow):
    for sRegister, sDirection in oRow.registers:
        if sDirection == SENDS:
            return '-->'
    return '---'


def draw_connector_row(bJoinContinues, bTrunkContinues, oLayout):
    lMarks = []
    if bTrunkContinues:
        lMarks.append((oLayout.trunk, '|'))
    if bJoinContinues:
        lMarks.append((oLayout.join, '|'))
    return draw_blank_row(oLayout, lMarks)


def draw_blank_row_over(oText, oLayout):
    oText.write(oLayout.device_edge, '|')
    oText.write(oLayout.part_edge, '|')
    return oText.to_string()


def draw_plain_row(oRow, oLayout):
    oText = text_row.TextRow()
    oText.write(oLayout.port, oRow.port)
    return draw_trace_end(oText, oRow, oLayout)


def draw_trace_end(oText, oRow, oLayout):
    # The trace across the board, from the [X] on the device's edge to the [X] on the part's.
    if oRow.source_part_trace is not None:
        oText.write(oLayout.device_edge - 1, draw_source_traces(oRow, oLayout))
        return oText.to_string()
    sTrace = '[X] ' + draw_arrow(oRow.trace, oLayout.longest_trace_name + oLayout.arrow_stretch) + ' [X] ' + get_part_end(oRow.trace)
    oText.write(oLayout.device_edge - 1, sTrace)
    return oText.to_string()


def draw_source_traces(oRow, oLayout):
    # The source comes in from above to a + between the boxes, which sends its clock to both.
    sToDevice = '[X] <-- ' + oRow.trace.name + ' ---+--- ' + oRow.source_part_trace.name + ' '
    iDashes = oLayout.part_edge - (oLayout.device_edge - 1) - len(sToDevice) - 3
    return sToDevice + '-' * iDashes + '> [X] ' + oRow.source_part_trace.part_pin


def draw_sources(lLines, lRows, oLayout):
    # Each source's name sits in the gap of the top edge, over the + its clock comes in at.
    for oRow in lRows:
        if oRow.source_part_trace is not None:
            iJunction = oLayout.device_edge - 1 + len('[X] <-- ' + oRow.trace.name + ' ---')
            write_over(lLines, 0, iJunction - len(oRow.trace.source) // 2 - 1, '(' + oRow.trace.source + ')')
            write_over(lLines, 1, iJunction, 'v')
            write_over(lLines, 2, iJunction, '|')


def write_over(lLines, iLine, iColumn, sText):
    oRow = text_row.TextRow()
    oRow.write(0, lLines[iLine])
    oRow.write(iColumn, sText)
    lLines[iLine] = oRow.to_string()


def draw_arrow(oTrace, iLongestTraceName):
    iPadding = iLongestTraceName - len(oTrace.name)
    if is_bidirectional_trace(oTrace):
        return '<-- ' + oTrace.name + ' ' + '-' * (iPadding + 2) + '>'
    if is_input_trace(oTrace):
        return '<-- ' + oTrace.name + ' ' + '-' * (iPadding + 3)
    return '--- ' + oTrace.name + ' ' + '-' * (iPadding + 2) + '>'
