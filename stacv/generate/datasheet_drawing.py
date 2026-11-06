'''
Draws a pin's timing against one edge of its clock, for the datasheet.

The drawing is not to scale: the edge and each value are placed in time order, a fixed number of columns apart,
so a value is drawn on the side of the edge its sign puts it.  Each value has an arrow from the edge, with its symbol.

                                   ____________________
    O_DAC_SCLK  ____________________/

                     |<-- tCOmin -->|<-- tCOmax -->|
                _____ _____________________________ _____
    O_DAC_DATA  _____X#############################X_____

The clock and the data are each drawn on two lines.  In the data, # is where it may change and _ where it is valid;
each X is the limit a value gives.
'''

from stacv.generate import datasheet_pin

VALID = '_'
CHANGING = '#'
# Columns before the first point and after the last.
MARGIN = 5
MINIMUM_POINT_GAP = 15
# Each arrow holds its symbol between "|<-- " and " -->|".
ARROW_DECORATION = 9


class Marker():
    '''
    A value of the pin: where the data changes, in ns from the edge, and its symbol.
    '''

    def __init__(self, sSymbol, fTime):
        self.symbol = sSymbol
        self.time = fTime
        self.column = None


class Drawing():
    '''
    The values of a pin against an edge, and whether the data is valid or changing before, between and after them.
    '''

    def __init__(self, sClockName, sEdge, sDataName, lMarkers, lStates):
        self.clock_name = sClockName
        self.edge = sEdge
        self.data_name = sDataName
        self.markers = lMarkers
        self.states = lStates
        self.edge_column = None
        self.width = None


def draw(oDrawing):
    place_columns(oDrawing)
    iNameWidth = max(len(oDrawing.clock_name), len(oDrawing.data_name))
    lLines = []
    lLines.extend(draw_clock(oDrawing, iNameWidth))
    lLines.append('')
    lLines.extend(draw_arrows(oDrawing, iNameWidth))
    lLines.extend(draw_data(oDrawing, iNameWidth))
    return lLines


def place_columns(oDrawing):
    lTimes = find_point_times(oDrawing)
    iGap = find_point_gap(oDrawing)
    for oMarker in oDrawing.markers:
        oMarker.column = MARGIN + lTimes.index(oMarker.time) * iGap
    oDrawing.edge_column = MARGIN + lTimes.index(0.0) * iGap
    oDrawing.width = MARGIN + (len(lTimes) - 1) * iGap + MARGIN + 1


def find_point_times(oDrawing):
    lTimes = [0.0]
    for oMarker in oDrawing.markers:
        if oMarker.time not in lTimes:
            lTimes.append(oMarker.time)
    lTimes.sort()
    return lTimes


def find_point_gap(oDrawing):
    iGap = MINIMUM_POINT_GAP
    for oMarker in oDrawing.markers:
        iGap = max(iGap, len(oMarker.symbol) + ARROW_DECORATION)
    return iGap


def draw_clock(oDrawing, iNameWidth):
    lHigh = [' '] * oDrawing.width
    lLow = [' '] * oDrawing.width
    for iColumn in range(oDrawing.width):
        if iColumn == oDrawing.edge_column:
            continue
        if is_clock_high(oDrawing, iColumn):
            lHigh[iColumn] = '_'
        else:
            lLow[iColumn] = '_'
    lLow[oDrawing.edge_column] = find_edge_character(oDrawing.edge)
    lLines = []
    lLines.append(build_line('', iNameWidth, lHigh))
    lLines.append(build_line(oDrawing.clock_name, iNameWidth, lLow))
    return lLines


def is_clock_high(oDrawing, iColumn):
    # A rising edge is low before and high after; a falling edge the other way round.
    bAfterEdge = iColumn > oDrawing.edge_column
    if oDrawing.edge == datasheet_pin.RISING:
        return bAfterEdge
    return not bAfterEdge


def find_edge_character(sEdge):
    if sEdge == datasheet_pin.RISING:
        return '/'
    return '\\'


def draw_arrows(oDrawing, iNameWidth):
    lRows = []
    for oMarker in sort_longest_first(oDrawing):
        if oMarker.column == oDrawing.edge_column:
            continue
        add_arrow(lRows, oDrawing, oMarker)
    lLines = []
    for oRow in lRows:
        lLines.append(build_line('', iNameWidth, oRow.columns))
    return lLines


def sort_longest_first(oDrawing):
    # Arrows on either side of the edge share a row; on the same side, the longer is drawn above the shorter.
    lMarkers = []
    for oMarker in oDrawing.markers:
        iIndex = 0
        while iIndex < len(lMarkers) and find_arrow_length(oDrawing, lMarkers[iIndex]) >= find_arrow_length(oDrawing, oMarker):
            iIndex += 1
        lMarkers.insert(iIndex, oMarker)
    return lMarkers


def find_arrow_length(oDrawing, oMarker):
    return abs(oMarker.column - oDrawing.edge_column)


class ArrowRow():

    def __init__(self, iWidth):
        self.columns = [' '] * iWidth
        self.spans = []

    def has_room(self, iStart, iEnd):
        # Arrows may share an end, at the edge.
        for iSpanStart, iSpanEnd in self.spans:
            if iStart < iSpanEnd and iSpanStart < iEnd:
                return False
        return True


def add_arrow(lRows, oDrawing, oMarker):
    iStart = min(oMarker.column, oDrawing.edge_column)
    iEnd = max(oMarker.column, oDrawing.edge_column)
    oRow = find_row_with_room(lRows, oDrawing.width, iStart, iEnd)
    oRow.spans.append((iStart, iEnd))
    sArrow = build_arrow(oMarker.symbol, iEnd - iStart - 1)
    oRow.columns[iStart] = '|'
    oRow.columns[iEnd] = '|'
    for iOffset, sCharacter in enumerate(sArrow):
        oRow.columns[iStart + 1 + iOffset] = sCharacter


def find_row_with_room(lRows, iWidth, iStart, iEnd):
    for oRow in lRows:
        if oRow.has_room(iStart, iEnd):
            return oRow
    oRow = ArrowRow(iWidth)
    lRows.append(oRow)
    return oRow


def build_arrow(sSymbol, iLength):
    # <-- symbol -->, with the dashes either side sharing the room the symbol leaves.
    iDashes = iLength - len(sSymbol) - 4
    iLeftDashes = iDashes // 2
    iRightDashes = iDashes - iLeftDashes
    return '<' + '-' * iLeftDashes + ' ' + sSymbol + ' ' + '-' * iRightDashes + '>'


def draw_data(oDrawing, iNameWidth):
    lTop = ['_'] * oDrawing.width
    lBottom = []
    for iColumn in range(oDrawing.width):
        lBottom.append(find_state(oDrawing, iColumn))
    for oMarker in oDrawing.markers:
        lTop[oMarker.column] = ' '
        lBottom[oMarker.column] = 'X'
    lLines = []
    lLines.append(build_line('', iNameWidth, lTop))
    lLines.append(build_line(oDrawing.data_name, iNameWidth, lBottom))
    return lLines


def find_state(oDrawing, iColumn):
    # The states are before the first marker, between each pair, and after the last.
    iState = 0
    for oMarker in oDrawing.markers:
        if iColumn > oMarker.column:
            iState += 1
    return oDrawing.states[iState]


def build_line(sName, iNameWidth, lColumns):
    return f'  {sName:<{iNameWidth}}  {"".join(lColumns)}'.rstrip()
