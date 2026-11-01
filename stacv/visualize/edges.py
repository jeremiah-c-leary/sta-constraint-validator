'''
Draws the launch and capture clock edges of a port as text.
'''

import math

from stacv.output import number_format
from stacv.rules import edge_times
from stacv.rules import requirements
from stacv.visualize import edge_window
from stacv.visualize import text_row

CLOCK_NAME_WIDTH = 15
LOW_BEFORE_FIRST_EDGE = '__'
ORIGIN_COLUMN = CLOCK_NAME_WIDTH + len(LOW_BEFORE_FIRST_EDGE)
SHORTEST_HALF_PERIOD_COLUMNS = 6

# The edge diagrams a methodology can choose from.
CONTINUOUS_CLOCK = 'continuous clock'
FIRST_LAST_CLOCK = 'first last clock'


def draw_edges(oPort, sDiagramType):
    lWindows = draw_edge_diagram(oPort, sDiagramType)
    if sDiagramType == CONTINUOUS_CLOCK:
        return draw_continuous_clock_edges(oPort, lWindows[0])
    return draw_windowed_edges(oPort, lWindows)


def draw_continuous_clock_edges(oPort, oWindow):
    lLines = list(oWindow.lines)
    lLines.append('')
    lLines.append('')
    lLines.append(format_setup_requirement(oPort))
    lLines.append(format_hold_requirement(oPort))
    return lLines


def draw_windowed_edges(oPort, lWindows):
    # Each window is followed by the requirement it shows.
    dRequirements = {edge_window.SETUP: format_setup_requirement(oPort), edge_window.HOLD: format_hold_requirement(oPort)}
    return edge_window.join_windows(lWindows, dRequirements, '')


def draw_edge_diagram(oPort, sDiagramType):
    if sDiagramType == CONTINUOUS_CLOCK:
        return [edge_window.EdgeWindow(draw_continuous_clock_diagram(oPort), [edge_window.SETUP, edge_window.HOLD])]
    if sDiagramType == FIRST_LAST_CLOCK:
        return draw_first_last_clock_windows(oPort)
    raise ValueError(f'unknown edge diagram type: {sDiagramType}')


def draw_continuous_clock_diagram(oPort):
    fColumnsPerNanosecond = calculate_columns_per_nanosecond(oPort)
    iEndColumn = calculate_column(calculate_end_time(oPort), fColumnsPerNanosecond)
    lLines = []
    lLines.extend(draw_launch_clock(oPort.launch_clock, fColumnsPerNanosecond, iEndColumn))
    lLines.append(format_frequency(oPort.launch_clock.period))
    lLines.append(draw_setup_requirement(oPort, fColumnsPerNanosecond))
    lLines.append(draw_hold_requirement(oPort, fColumnsPerNanosecond))
    lLines.append('')
    lLines.extend(draw_capture_clock(oPort.capture_clock, fColumnsPerNanosecond, iEndColumn))
    lLines.append(format_frequency(oPort.capture_clock.period))
    return lLines


def draw_first_last_clock_windows(oPort):
    # The setup window starts the capture clock at its first pulse, and the hold window stops it after its last pulse.
    fColumnsPerNanosecond = calculate_columns_per_nanosecond(oPort)
    oCaptureClock = oPort.capture_clock
    iFirstPulseStart = find_pulse_start(oCaptureClock.idle, convert_capture_edge(oCaptureClock.setup_edge))
    iFirstPulseEnd = iFirstPulseStart + 1
    iLastPulseEnd = find_pulse_start(oCaptureClock.idle, convert_capture_edge(oCaptureClock.hold_edge)) + 1
    iEndColumn = calculate_column(calculate_first_last_clock_end_time(oPort, iFirstPulseEnd), fColumnsPerNanosecond)
    iLastEdgeInWindow = find_last_edge(oCaptureClock.period, fColumnsPerNanosecond, iEndColumn)
    lSetupLines = draw_launch_clock_with_frequency(oPort.launch_clock, fColumnsPerNanosecond, iEndColumn)
    lSetupLines.append(draw_setup_requirement(oPort, fColumnsPerNanosecond))
    lSetupLines.append(draw_edge_marker('first clock edge', calculate_edge_column(oCaptureClock.period, iFirstPulseStart, fColumnsPerNanosecond)))
    lSetupLines.append('')
    lSetupLines.extend(draw_stopped_clock(oCaptureClock, fColumnsPerNanosecond, iEndColumn, iFirstPulseStart, iLastEdgeInWindow))
    lSetupLines.append(format_frequency(oCaptureClock.period))
    lHoldLines = draw_launch_clock_with_frequency(oPort.launch_clock, fColumnsPerNanosecond, iEndColumn)
    lHoldLines.append(draw_hold_requirement(oPort, fColumnsPerNanosecond))
    lHoldLines.append(draw_edge_marker('last clock edge', calculate_edge_column(oCaptureClock.period, iLastPulseEnd, fColumnsPerNanosecond)))
    lHoldLines.append('')
    lHoldLines.extend(draw_stopped_clock(oCaptureClock, fColumnsPerNanosecond, iEndColumn, 0, iLastPulseEnd))
    lHoldLines.append(format_frequency(oCaptureClock.period))
    lWindows = []
    lWindows.append(edge_window.EdgeWindow(lSetupLines, [edge_window.SETUP]))
    lWindows.append(edge_window.EdgeWindow(lHoldLines, [edge_window.HOLD]))
    return lWindows


def convert_capture_edge(sEdgeLetter):
    return edge_times.convert_edge_letter_to_number(sEdgeLetter)


def find_pulse_start(sIdle, iEdgeNumber):
    # A clock that idles low pulses high, rising then falling; one that idles high pulses low.
    # Each pulse is two edges, so it ends on the edge after its start.
    if starts_pulse(sIdle, iEdgeNumber):
        return iEdgeNumber
    return iEdgeNumber - 1


def starts_pulse(sIdle, iEdgeNumber):
    if sIdle == 'low':
        return is_rising_edge(iEdgeNumber)
    return not is_rising_edge(iEdgeNumber)


def calculate_first_last_clock_end_time(oPort, iFirstPulseEnd):
    # Both windows end where the first pulse ends, or later if an edge of the port is later.
    lEdgeTimes = []
    lEdgeTimes.append(edge_times.calculate_edge_time(oPort.capture_clock.period, iFirstPulseEnd))
    lEdgeTimes.append(calculate_launch_edge_time(oPort.launch_clock, oPort.launch_clock.setup_edge))
    lEdgeTimes.append(calculate_launch_edge_time(oPort.launch_clock, oPort.launch_clock.hold_edge))
    lEdgeTimes.append(calculate_capture_edge_time(oPort.capture_clock, oPort.capture_clock.setup_edge))
    lEdgeTimes.append(calculate_capture_edge_time(oPort.capture_clock, oPort.capture_clock.hold_edge))
    return max(lEdgeTimes)


def draw_launch_clock_with_frequency(oLaunchClock, fColumnsPerNanosecond, iEndColumn):
    lLines = draw_launch_clock(oLaunchClock, fColumnsPerNanosecond, iEndColumn)
    lLines.append(format_frequency(oLaunchClock.period))
    return lLines


def draw_edge_marker(sText, iColumn):
    # Points at the edge from the left, or from the right when the left has no room.
    oRow = text_row.TextRow()
    sLeftMarker = sText + ' ---->'
    if len(sLeftMarker) <= iColumn:
        oRow.write(iColumn - len(sLeftMarker), sLeftMarker + '|')
    else:
        oRow.write(iColumn, '|<---- ' + sText)
    return oRow.to_string()


def draw_stopped_clock(oClock, fColumnsPerNanosecond, iEndColumn, iFirstEdge, iLastEdge):
    # Runs from the first edge to the last edge, and is idle outside them.
    oLabelRow = text_row.TextRow()
    oWaveRow = text_row.TextRow()
    oWaveRow.write(0, oClock.name.ljust(CLOCK_NAME_WIDTH))
    iFirstColumn = calculate_edge_column(oClock.period, iFirstEdge, fColumnsPerNanosecond)
    if iFirstEdge == 0:
        oWaveRow.write(CLOCK_NAME_WIDTH, LOW_BEFORE_FIRST_EDGE)
    else:
        draw_idle(oClock.idle, oLabelRow, oWaveRow, CLOCK_NAME_WIDTH, iFirstColumn - 1)
    for iEdgeNumber in range(iFirstEdge, iLastEdge + 1):
        draw_running_edge(oClock.period, iEdgeNumber, iLastEdge, oLabelRow, oWaveRow, fColumnsPerNanosecond, iEndColumn)
    iLastColumn = calculate_edge_column(oClock.period, iLastEdge, fColumnsPerNanosecond)
    if iLastColumn < iEndColumn:
        draw_idle(oClock.idle, oLabelRow, oWaveRow, iLastColumn + 1, iEndColumn)
    return [oLabelRow.to_string(), oWaveRow.to_string()]


def draw_running_edge(fPeriod, iEdgeNumber, iLastEdge, oLabelRow, oWaveRow, fColumnsPerNanosecond, iEndColumn):
    iColumn = calculate_edge_column(fPeriod, iEdgeNumber, fColumnsPerNanosecond)
    oLabelRow.write(iColumn, edge_times.convert_edge_number_to_letter(iEdgeNumber))
    oWaveRow.write(iColumn, '|')
    if iEdgeNumber == iLastEdge:
        return
    iSegmentEndColumn = calculate_segment_end_column(fPeriod, iEdgeNumber, fColumnsPerNanosecond, iEndColumn)
    sSegment = '_' * (iSegmentEndColumn - iColumn - 1)
    if is_rising_edge(iEdgeNumber):
        oLabelRow.write(iColumn + 1, sSegment)
    else:
        oWaveRow.write(iColumn + 1, sSegment)


def draw_idle(sIdle, oLabelRow, oWaveRow, iFirstColumn, iLastColumn):
    # A high level is drawn in the label row, above the wave, as the high half of a pulse is.
    sLevel = '_' * (iLastColumn - iFirstColumn + 1)
    if sIdle == 'high':
        oLabelRow.write(iFirstColumn, sLevel)
    else:
        oWaveRow.write(iFirstColumn, sLevel)


def format_setup_requirement(oPort):
    fRequirement = requirements.calculate_configuration_setup_requirement(oPort)
    return f'setup requirement = {number_format.format_number(fRequirement)} ns'


def format_hold_requirement(oPort):
    fRequirement = requirements.calculate_configuration_hold_requirement(oPort)
    return f'hold requirement = {number_format.format_number(fRequirement)} ns'


def format_frequency(fPeriod):
    return f'({number_format.format_number(1000 / fPeriod)} MHz)'


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
        lEdgeLabels.append(edge_times.convert_edge_number_to_letter(iEdgeNumber))
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
