'''
Draws the eye of a port from its timing reports: the time its data is stable around the capture edge.

Times are measured from the capture edge at the endpoint, the part's pin for an output and the capturing register for an input:

    the data settles     setup time + setup slack    before the edge
    the data changes     hold time + hold slack      after the edge

The setup and hold times are the part pin's for an output, and the register's library setup and hold for an input.
Between the changes the data is stable, the eye; the setup and hold window is best centred in it, with equal slacks.
Its offset from the centre of the eye is (setup slack - hold slack) / 2: negative when the window is early, so the capture should be later.

A methodology without one setup and hold window, such as SDR-SS-O-FLC, has no eye, and says so instead.

Each process corner is a row, timed from its worst setup and worst hold timing report, and the last row combines them:
its eye is what every corner leaves.

The data changes within a window, the time from the hold capture edge to the setup capture edge less the spread of the delays:

    window = (setup requirement - hold requirement) - (maximum delay - minimum delay)

What the slacks do not use of the window is how long the data takes to change, which sets where each row's eye ends.
'''

from stacv.methodology import methodology
from stacv.methodology import methodology_factory
from stacv.output import number_format
from stacv.rules import part_timing
from stacv.rules import path_lookups

EYE_WIDTH = 40
ROW_NAME_WIDTH = 4
COMBINED_ROW = 'All'
# The numbers start after the row name and the eye, each followed by two spaces.
NUMBERS_COLUMN = 4 + ROW_NAME_WIDTH + 2 + EYE_WIDTH + 1 + 2


class EyeRow():
    '''
    One process corner, or every corner combined, of a port's eye.
    '''

    def __init__(self, sName, fSetupSlack, fHoldSlack, fSetupTime, fHoldTime, fWindow):
        self.name = sName
        self.setup_slack = fSetupSlack
        self.hold_slack = fHoldSlack
        self.setup_time = fSetupTime
        self.hold_time = fHoldTime
        self.window = fWindow

    def get_settle_time(self):
        # How long before the capture edge the data settles.
        return self.setup_time + self.setup_slack

    def get_change_time(self):
        # How long after the capture edge the data changes.
        return self.hold_time + self.hold_slack

    def get_change_length(self):
        # How long the data takes to change: what the slacks leave of the window.
        return max(0.0, self.window - self.setup_slack - self.hold_slack)

    def get_left_extent(self):
        return max(self.get_settle_time() + self.get_change_length(), self.setup_time)

    def get_right_extent(self):
        return max(self.get_change_time() + self.get_change_length(), self.hold_time)

    def get_offset(self):
        return (self.setup_slack - self.hold_slack) / 2


def draw_eye(oPortProfile):
    oMethodology = methodology_factory.create_methodology(oPortProfile.port.methodology)
    if oMethodology.no_eye_reason is not None:
        return [f'{oPortProfile.port.name} ({oPortProfile.port.methodology}): no eye, {oMethodology.no_eye_reason}']
    lRows = build_rows(oPortProfile)
    fLeft = find_left_extent(lRows)
    fColumnsPerNanosecond = EYE_WIDTH / (fLeft + find_right_extent(lRows))
    lLines = []
    lLines.append(f'{oPortProfile.port.name} ({oPortProfile.port.methodology})')
    lLines.append(f'  setup {format_time(find_largest_setup_time(lRows))}, hold {format_time(find_largest_hold_time(lRows))}, {1 / fColumnsPerNanosecond:.2f} ns a character')
    lLines.append(build_number_heading())
    for oRow in lRows:
        lLines.append(draw_row(oRow, fLeft, fColumnsPerNanosecond))
    return lLines


def build_rows(oPortProfile):
    fWindow = calculate_window(oPortProfile)
    lSetupReports = oPortProfile.timing_reports.get_setup_reports()
    lHoldReports = oPortProfile.timing_reports.get_hold_reports()
    lRows = []
    for sCorner in find_process_corners(oPortProfile.timing_reports.reports):
        oSetupReport = find_worst_report(lSetupReports, sCorner)
        oHoldReport = find_worst_report(lHoldReports, sCorner)
        lRows.append(build_row(sCorner, oSetupReport, oHoldReport, oPortProfile, fWindow))
    oSetupReport = find_worst_report(lSetupReports, None)
    oHoldReport = find_worst_report(lHoldReports, None)
    lRows.append(build_row(COMBINED_ROW, oSetupReport, oHoldReport, oPortProfile, fWindow))
    return lRows


def build_row(sName, oSetupReport, oHoldReport, oPortProfile, fWindow):
    fSetupTime = find_setup_time(oPortProfile, oSetupReport)
    fHoldTime = find_hold_time(oPortProfile, oHoldReport)
    return EyeRow(sName, oSetupReport.slack, oHoldReport.slack, fSetupTime, fHoldTime, fWindow)


def calculate_window(oPortProfile):
    # A previous rule ensures every setup, or every hold, timing report gives the same delay and requirement.
    oSetupReport = oPortProfile.timing_reports.get_setup_reports()[0]
    oHoldReport = oPortProfile.timing_reports.get_hold_reports()[0]
    sDelay = get_delay_name(oPortProfile.port)
    fDelaySpread = getattr(oSetupReport, sDelay) - getattr(oHoldReport, sDelay)
    return oSetupReport.requirement - oHoldReport.requirement - fDelaySpread


def get_delay_name(oPort):
    if oPort.data_direction == methodology.INPUT:
        return 'input_delay'
    return 'output_delay'


def find_setup_time(oPortProfile, oSetupReport):
    # The part's pin captures an output; a register captures an input.
    if oPortProfile.port.data_direction == methodology.INPUT:
        return oSetupReport.library_requirement
    oPin = path_lookups.get_part_data_pin(oPortProfile)
    return part_timing.get_setup(oPin, oPortProfile.port).value


def find_hold_time(oPortProfile, oHoldReport):
    if oPortProfile.port.data_direction == methodology.INPUT:
        return oHoldReport.library_requirement
    oPin = path_lookups.get_part_data_pin(oPortProfile)
    return part_timing.get_hold(oPin, oPortProfile.port).value


def find_process_corners(lTimingReports):
    # The corners in the order the timing reports first give them.
    lCorners = []
    for oTimingReport in lTimingReports:
        if oTimingReport.process_corner not in lCorners:
            lCorners.append(oTimingReport.process_corner)
    return lCorners


def find_worst_report(lTimingReports, sCorner):
    # The report with the least slack at the corner, or at every corner when the corner is None.
    oWorstReport = None
    for oTimingReport in lTimingReports:
        if sCorner is not None and oTimingReport.process_corner != sCorner:
            continue
        if oWorstReport is None or oTimingReport.slack < oWorstReport.slack:
            oWorstReport = oTimingReport
    return oWorstReport


def find_left_extent(lRows):
    fExtent = 0.0
    for oRow in lRows:
        fExtent = max(fExtent, oRow.get_left_extent())
    return fExtent


def find_right_extent(lRows):
    fExtent = 0.0
    for oRow in lRows:
        fExtent = max(fExtent, oRow.get_right_extent())
    return fExtent


def find_largest_setup_time(lRows):
    fTime = lRows[0].setup_time
    for oRow in lRows:
        fTime = max(fTime, oRow.setup_time)
    return fTime


def find_largest_hold_time(lRows):
    fTime = lRows[0].hold_time
    for oRow in lRows:
        fTime = max(fTime, oRow.hold_time)
    return fTime


def build_number_heading():
    return ' ' * NUMBERS_COLUMN + f'{"setup slack":>11}  {"hold slack":>10}  {"offset from eye centre":>22}'


def draw_row(oRow, fLeft, fColumnsPerNanosecond):
    sEye = draw_row_eye(oRow, fLeft, fColumnsPerNanosecond)
    sNumbers = f'{oRow.setup_slack:8.3f} ns  {oRow.hold_slack:7.3f} ns  {oRow.get_offset():+19.3f} ns'
    return f'    {oRow.name:{ROW_NAME_WIDTH}}  {sEye}  {sNumbers}'


def draw_row_eye(oRow, fLeft, fColumnsPerNanosecond):
    # Column 0 is fLeft ns before the capture edge.  Only the eye matters, so the changes are drawn out to the ends,
    # and the end columns are always changes, so the eye ends at an X even when a change is shorter than a column.
    lColumns = ['X'] * (EYE_WIDTH + 1)
    iSettleColumn = max(1, find_column(-oRow.get_settle_time(), fLeft, fColumnsPerNanosecond))
    iChangeColumn = min(EYE_WIDTH - 1, find_column(oRow.get_change_time(), fLeft, fColumnsPerNanosecond))
    for iColumn in range(iSettleColumn, iChangeColumn + 1):
        write_column(lColumns, iColumn, '.')
    iEdgeColumn = find_column(0.0, fLeft, fColumnsPerNanosecond)
    draw_setup_and_hold_window(lColumns, iEdgeColumn, oRow, fColumnsPerNanosecond)
    write_column(lColumns, iEdgeColumn, '|')
    return ''.join(lColumns)


def draw_setup_and_hold_window(lColumns, iEdgeColumn, oRow, fColumnsPerNanosecond):
    # The data must be stable from the setup time before the edge to the hold time after it.  A negative setup or hold
    # time puts that end on the other side of the edge.  < marks the start and > the end; a zero time has no mark.
    iStartColumn = find_window_end_column(iEdgeColumn, -oRow.setup_time, fColumnsPerNanosecond)
    iEndColumn = find_window_end_column(iEdgeColumn, oRow.hold_time, fColumnsPerNanosecond)
    if oRow.setup_time != 0 and oRow.hold_time != 0 and iEndColumn <= iStartColumn:
        iEndColumn = iStartColumn + 1
    for iColumn in range(iStartColumn + 1, iEndColumn):
        write_column(lColumns, iColumn, '-')
    if oRow.setup_time != 0:
        write_column(lColumns, iStartColumn, '<')
    if oRow.hold_time != 0:
        write_column(lColumns, iEndColumn, '>')


def find_window_end_column(iEdgeColumn, fTime, fColumnsPerNanosecond):
    # A time too short for a column is still a column from the edge, so the reader sees it is there.
    iOffset = round(fTime * fColumnsPerNanosecond)
    if fTime > 0:
        return iEdgeColumn + max(1, iOffset)
    if fTime < 0:
        return iEdgeColumn + min(-1, iOffset)
    return iEdgeColumn


def find_column(fTime, fLeft, fColumnsPerNanosecond):
    return round((fTime + fLeft) * fColumnsPerNanosecond)


def write_column(lColumns, iColumn, sCharacter):
    if 0 <= iColumn < len(lColumns):
        lColumns[iColumn] = sCharacter


def format_time(fTime):
    return f'{number_format.format_number(fTime)} ns'
