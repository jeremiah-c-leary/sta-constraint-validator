'''
Draws the device, the part and the traces between them as text.
'''

from stacv.visualize import text_row

DEVICE_NAME = 'Device'
INDENT = '  '
MARGIN = 2
ARROW_LENGTH_AROUND_NAME = 8


def draw_block_diagram(oInterface, oTraceList, oPart):
    lTraces = select_traces(oInterface, oTraceList)
    iDeviceEdge = calculate_device_edge(lTraces)
    iLongestTraceName = find_longest_trace_name(lTraces)
    iPartEdge = calculate_part_edge(iDeviceEdge, iLongestTraceName)
    iPartWidth = calculate_part_width(oPart.part_number, lTraces)
    sBorder = draw_border(iDeviceEdge, iPartEdge, iPartWidth)
    sBlankRow = draw_blank_row(iDeviceEdge, iPartEdge)
    lLines = []
    lLines.append(sBorder)
    lLines.append(draw_label_row(oPart.part_number, iDeviceEdge, iPartEdge))
    lLines.append(sBlankRow)
    for oTrace in lTraces:
        lLines.append(draw_trace_row(oTrace, iDeviceEdge, iLongestTraceName))
        lLines.append(sBlankRow)
    lLines.append(sBorder)
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


def calculate_device_edge(lTraces):
    lNames = [DEVICE_NAME]
    for oTrace in lTraces:
        lNames.append(get_device_end(oTrace))
    return len(INDENT) + find_longest(lNames) + MARGIN


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


def draw_blank_row(iDeviceEdge, iPartEdge):
    oRow = text_row.TextRow()
    oRow.write(iDeviceEdge, '|')
    oRow.write(iPartEdge, '|')
    return oRow.to_string()


def draw_label_row(sPartNumber, iDeviceEdge, iPartEdge):
    oRow = text_row.TextRow()
    oRow.write(len(INDENT), DEVICE_NAME)
    oRow.write(iDeviceEdge, '|')
    oRow.write(iPartEdge, '|' + INDENT + sPartNumber)
    return oRow.to_string()


def draw_trace_row(oTrace, iDeviceEdge, iLongestTraceName):
    oRow = text_row.TextRow()
    oRow.write(len(INDENT), get_device_end(oTrace))
    oRow.write(iDeviceEdge - 1, '[X] ' + draw_arrow(oTrace, iLongestTraceName) + ' [X] ' + get_part_end(oTrace))
    return oRow.to_string()


def draw_arrow(oTrace, iLongestTraceName):
    iPadding = iLongestTraceName - len(oTrace.name)
    if is_bidirectional_trace(oTrace):
        return '<-- ' + oTrace.name + ' ' + '-' * (iPadding + 2) + '>'
    if is_input_trace(oTrace):
        return '<-- ' + oTrace.name + ' ' + '-' * (iPadding + 3)
    return '--- ' + oTrace.name + ' ' + '-' * (iPadding + 2) + '>'
