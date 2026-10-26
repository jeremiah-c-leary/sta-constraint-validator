'''
Draws the launch and capture clock edges of a port as text.
'''

import math

from stacv.rules import edge_times
from stacv.visualize import text_row

CLOCK_NAME_WIDTH = 15
LOW_BEFORE_FIRST_EDGE = '__'
ORIGIN_COLUMN = CLOCK_NAME_WIDTH + len(LOW_BEFORE_FIRST_EDGE)
SHORTEST_HALF_PERIOD_COLUMNS = 6


def draw_edges(oPort):
    fColumnsPerNanosecond = calculate_columns_per_nanosecond(oPort)
    iEndColumn = calculate_column(calculate_end_time(oPort), fColumnsPerNanosecond)
    lLines = []
    lLines.extend(draw_launch_clock(oPort.launch_clock, fColumnsPerNanosecond, iEndColumn))
    lLines.append('')
    lLines.append(draw_setup_requirement(oPort, fColumnsPerNanosecond))
    lLines.append(draw_hold_requirement(oPort, fColumnsPerNanosecond))
    lLines.append('')
    lLines.extend(draw_capture_clock(oPort.capture_clock, fColumnsPerNanosecond, iEndColumn))
    return lLines


def calculate_columns_per_nanosecond(oPort):
    fLaunchHalfPeriod = oPort.launch_clock.period / 2
    fCaptureHalfPeriod = oPort.capture_clock.period / 2
    return SHORTEST_HALF_PERIOD_COLUMNS / min(fLaunchHalfPeriod, fCaptureHalfPeriod)


def calculate_end_time(oPort):
    lEdgeTimes = []
    lEdgeTimes.append(calculate_launch_edge_time(oPort.launch_clock, oPort.launch_clock.setup_edge))
    lEdgeTimes.append(calculate_launch_edge_time(oPort.launch_clock, oPort.launch_clock.hold_edge))
    lEdgeTimes.append(calculate_capture_edge_time(oPort.capture_clock, oPort.capture_clock.setup_edge))
    lEdgeTimes.append(calculate_capture_edge_time(oPort.capture_clock, oPort.capture_clock.hold_edge))
    return find_next_capture_edge_time(oPort.capture_clock, max(lEdgeTimes))


def find_next_capture_edge_time(oCaptureClock, fTime):
    iEdgeNumber = 0
    while edge_times.calculate_edge_time(oCaptureClock.period, iEdgeNumber) <= fTime:
        iEdgeNumber += 1
    return edge_times.calculate_edge_time(oCaptureClock.period, iEdgeNumber)


def calculate_launch_edge_time(oLaunchClock, iEdgeNumber):
    return edge_times.calculate_edge_time(oLaunchClock.period, iEdgeNumber)


def calculate_capture_edge_time(oCaptureClock, sEdgeLetter):
    iEdgeNumber = edge_times.convert_edge_letter_to_number(sEdgeLetter)
    return edge_times.calculate_edge_time(oCaptureClock.period, iEdgeNumber)


def calculate_column(fTime, fColumnsPerNanosecond):
    # Rounds half a column up; round() would round half to the nearest even column.
    return ORIGIN_COLUMN + math.floor(fTime * fColumnsPerNanosecond + 0.5)


def calculate_edge_column(fPeriod, iEdgeNumber, fColumnsPerNanosecond):
    fEdgeTime = edge_times.calculate_edge_time(fPeriod, iEdgeNumber)
    return calculate_column(fEdgeTime, fColumnsPerNanosecond)


def draw_launch_clock(oLaunchClock, fColumnsPerNanosecond, iEndColumn):
    iLastEdge = find_last_edge(oLaunchClock.period, fColumnsPerNanosecond, iEndColumn)
    lEdgeLabels = build_launch_edge_labels(iLastEdge)
    return draw_clock(oLaunchClock.name, oLaunchClock.period, lEdgeLabels, fColumnsPerNanosecond, iEndColumn)


def draw_capture_clock(oCaptureClock, fColumnsPerNanosecond, iEndColumn):
    iLastEdge = find_last_edge(oCaptureClock.period, fColumnsPerNanosecond, iEndColumn)
    lEdgeLabels = build_capture_edge_labels(iLastEdge)
    return draw_clock(oCaptureClock.name, oCaptureClock.period, lEdgeLabels, fColumnsPerNanosecond, iEndColumn)


def find_last_edge(fPeriod, fColumnsPerNanosecond, iEndColumn):
    iEdgeNumber = 0
    while calculate_edge_column(fPeriod, iEdgeNumber + 1, fColumnsPerNanosecond) <= iEndColumn:
        iEdgeNumber += 1
    return iEdgeNumber


def build_launch_edge_labels(iLastEdge):
    lEdgeLabels = []
    for iEdgeNumber in range(iLastEdge + 1):
        lEdgeLabels.append(str(iEdgeNumber))
    return lEdgeLabels


def build_capture_edge_labels(iLastEdge):
    lEdgeLabels = []
    for iEdgeNumber in range(iLastEdge + 1):
        lEdgeLabels.append(chr(ord('A') + iEdgeNumber))
    return lEdgeLabels


def draw_clock(sName, fPeriod, lEdgeLabels, fColumnsPerNanosecond, iEndColumn):
    oTensRow = text_row.TextRow()
    oLabelRow = text_row.TextRow()
    oWaveRow = text_row.TextRow()
    oWaveRow.write(0, sName.ljust(CLOCK_NAME_WIDTH) + LOW_BEFORE_FIRST_EDGE)
    for iEdgeNumber, sEdgeLabel in enumerate(lEdgeLabels):
        iColumn = calculate_edge_column(fPeriod, iEdgeNumber, fColumnsPerNanosecond)
        iSegmentEndColumn = calculate_segment_end_column(fPeriod, iEdgeNumber, fColumnsPerNanosecond, iEndColumn)
        draw_edge_label(oTensRow, oLabelRow, iColumn, sEdgeLabel)
        oWaveRow.write(iColumn, '|')
        sSegment = '_' * (iSegmentEndColumn - iColumn - 1)
        if is_rising_edge(iEdgeNumber):
            oLabelRow.write(iColumn + 1, sSegment)
        else:
            oWaveRow.write(iColumn + 1, sSegment)
    return build_clock_lines(oTensRow, oLabelRow, oWaveRow)


def calculate_segment_end_column(fPeriod, iEdgeNumber, fColumnsPerNanosecond, iEndColumn):
    iNextColumn = calculate_edge_column(fPeriod, iEdgeNumber + 1, fColumnsPerNanosecond)
    return min(iNextColumn, iEndColumn)


def draw_edge_label(oTensRow, oLabelRow, iColumn, sEdgeLabel):
    oLabelRow.write(iColumn, sEdgeLabel[-1])
    if has_tens_digit(sEdgeLabel):
        oTensRow.write(iColumn, sEdgeLabel[-2])


def has_tens_digit(sEdgeLabel):
    return len(sEdgeLabel) > 1


def is_rising_edge(iEdgeNumber):
    return iEdgeNumber % 2 == 0


def build_clock_lines(oTensRow, oLabelRow, oWaveRow):
    lLines = []
    if not oTensRow.is_empty():
        lLines.append(oTensRow.to_string())
    lLines.append(oLabelRow.to_string())
    lLines.append(oWaveRow.to_string())
    return lLines


def draw_setup_requirement(oPort, fColumnsPerNanosecond):
    fLaunchTime = calculate_launch_edge_time(oPort.launch_clock, oPort.launch_clock.setup_edge)
    fCaptureTime = calculate_capture_edge_time(oPort.capture_clock, oPort.capture_clock.setup_edge)
    iLaunchColumn = calculate_column(fLaunchTime, fColumnsPerNanosecond)
    iCaptureColumn = calculate_column(fCaptureTime, fColumnsPerNanosecond)
    return draw_requirement('setup requirement', iLaunchColumn, iCaptureColumn)


def draw_hold_requirement(oPort, fColumnsPerNanosecond):
    fLaunchTime = calculate_launch_edge_time(oPort.launch_clock, oPort.launch_clock.hold_edge)
    fCaptureTime = calculate_capture_edge_time(oPort.capture_clock, oPort.capture_clock.hold_edge)
    iLaunchColumn = calculate_column(fLaunchTime, fColumnsPerNanosecond)
    iCaptureColumn = calculate_column(fCaptureTime, fColumnsPerNanosecond)
    return draw_requirement('hold requirement', iLaunchColumn, iCaptureColumn)


def draw_requirement(sText, iLaunchColumn, iCaptureColumn):
    oRow = text_row.TextRow()
    if iLaunchColumn == iCaptureColumn:
        oRow.write(iLaunchColumn, '| ' + sText)
        return oRow.to_string()
    draw_arrow(oRow, iLaunchColumn, iCaptureColumn)
    write_requirement_text(oRow, sText, iLaunchColumn, iCaptureColumn)
    return oRow.to_string()


def draw_arrow(oRow, iLaunchColumn, iCaptureColumn):
    iFirstColumn = min(iLaunchColumn, iCaptureColumn)
    iLastColumn = max(iLaunchColumn, iCaptureColumn)
    oRow.write(iFirstColumn, '-' * (iLastColumn - iFirstColumn))
    if iCaptureColumn > iLaunchColumn:
        oRow.write(iCaptureColumn - 1, '>')
    else:
        oRow.write(iCaptureColumn + 1, '<')
    oRow.write(iFirstColumn, '|')
    oRow.write(iLastColumn, '|')


def write_requirement_text(oRow, sText, iLaunchColumn, iCaptureColumn):
    iDashCount = abs(iCaptureColumn - iLaunchColumn) - 2
    if not text_fits_in_arrow(sText, iDashCount):
        oRow.write(max(iLaunchColumn, iCaptureColumn) + 2, sText)
        return
    iTextColumn = find_first_dash_column(iLaunchColumn, iCaptureColumn) + (iDashCount - len(sText) + 1) // 2
    oRow.write(iTextColumn, sText)


def text_fits_in_arrow(sText, iDashCount):
    # Keeps at least one dash on each side of the text.
    return len(sText) <= iDashCount - 2


def find_first_dash_column(iLaunchColumn, iCaptureColumn):
    if iCaptureColumn > iLaunchColumn:
        return iLaunchColumn + 1
    return iCaptureColumn + 2
