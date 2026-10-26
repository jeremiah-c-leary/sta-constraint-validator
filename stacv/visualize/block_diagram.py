'''
Draws the device, the part and the traces between them as text.
'''

from stacv.visualize import text_row

DEVICE_NAME = 'Device'
INDENT = '  '
MARGIN = 2
ARROW_LENGTH_AROUND_NAME = 8


def draw_block_diagram(oInterface, oTraceList, oPart):
    lTraces = order_traces(oTraceList.traces, find_clock_port(oInterface))
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


def find_clock_port(oInterface):
    # An interface has one clock, so every port names the same clock port.
    return oInterface.ports[0].capture_clock.port


def order_traces(lTraces, sClockPort):
    lOrderedTraces = []
    lOrderedTraces.extend(select_output_traces(lTraces, sClockPort))
    lOrderedTraces.extend(select_input_traces(lTraces))
    lOrderedTraces.extend(select_clock_traces(lTraces, sClockPort))
    return lOrderedTraces


def select_output_traces(lTraces, sClockPort):
    lOutputTraces = []
    for oTrace in lTraces:
        if not is_input_trace(oTrace) and not is_clock_trace(oTrace, sClockPort):
            lOutputTraces.append(oTrace)
    return lOutputTraces


def select_input_traces(lTraces):
    lInputTraces = []
    for oTrace in lTraces:
        if is_input_trace(oTrace):
            lInputTraces.append(oTrace)
    return lInputTraces


def select_clock_traces(lTraces, sClockPort):
    lClockTraces = []
    for oTrace in lTraces:
        if is_clock_trace(oTrace, sClockPort):
            lClockTraces.append(oTrace)
    return lClockTraces


def is_input_trace(oTrace):
    return oTrace.device_to_part is None


def is_bidirectional_trace(oTrace):
    return oTrace.device_to_part is not None and oTrace.part_to_device is not None


def is_clock_trace(oTrace, sClockPort):
    return oTrace.device_pin == sClockPort


def calculate_device_edge(lTraces):
    lNames = [DEVICE_NAME]
    for oTrace in lTraces:
        lNames.append(oTrace.device_pin)
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
        lNames.append(oTrace.part_pin)
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
    oRow.write(len(INDENT), oTrace.device_pin)
    oRow.write(iDeviceEdge - 1, '[X] ' + draw_arrow(oTrace, iLongestTraceName) + ' [X] ' + oTrace.part_pin)
    return oRow.to_string()


def draw_arrow(oTrace, iLongestTraceName):
    iPadding = iLongestTraceName - len(oTrace.name)
    if is_bidirectional_trace(oTrace):
        return '<-- ' + oTrace.name + ' ' + '-' * (iPadding + 2) + '>'
    if is_input_trace(oTrace):
        return '<-- ' + oTrace.name + ' ' + '-' * (iPadding + 3)
    return '--- ' + oTrace.name + ' ' + '-' * (iPadding + 2) + '>'
