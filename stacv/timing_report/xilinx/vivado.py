
from stacv.timing_report import timing_report
from stacv.timing_report import timing_report_file
from stacv.timing_report import timing_report_list
from stacv.timing_report import timing_report_parse_error
from stacv.timing_report import delay_element
from stacv.timing_report import delay_path


TOTAL_NUMBER_OF_SEPARATORS = 5


def parse_timing_report(oTimingReportFile):
    validate_timing_report_file(oTimingReportFile)
    oTimingReports = timing_report_list.TimingReportList()
    for oTimingReportText in extract_timing_report_texts(oTimingReportFile):
        validate_timing_report_text(oTimingReportText)
        oTimingReport = create_timing_report(oTimingReportText)
        populate_timing_report(oTimingReport)
        oTimingReports.add(oTimingReport)
    return oTimingReports


def extract_timing_report_texts(oTimingReportFile):
    lTimingReports = []
    lReport = None
    for oLine in oTimingReportFile.lines:
        if is_start_of_timing_report(oLine):
            lReport = []
        if lReport is None:
            continue
        lReport.append(oLine)
        if is_end_of_timing_report(oLine):
            oTimingReportText = timing_report_file.TimingReportText(oTimingReportFile, lReport)
            lTimingReports.append(oTimingReportText)
            lReport = None

    return lTimingReports


def validate_timing_report_file(oTimingReportFile):
    check_timing_reports_exist(oTimingReportFile)
    check_ending_of_timing_report_without_beginning(oTimingReportFile)
    check_beginning_of_timing_report_without_ending(oTimingReportFile)


def check_timing_reports_exist(oTimingReportFile):
    bStart = False
    for oLine in oTimingReportFile.lines:
        if is_start_of_timing_report(oLine):
            bStart = True
            break

    if len(oTimingReportFile.lines) == 0:
        raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_001', timing_report_file.ReportLine(oTimingReportFile.filename, '', 1), 'No timing reports detected')

    if not bStart:
        raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_001', oTimingReportFile.lines[0], 'No timing reports detected')


def check_ending_of_timing_report_without_beginning(oTimingReportFile):
    bStart = False
    for oLine in oTimingReportFile.lines:
        if is_end_of_timing_report(oLine):
            if not bStart:
                raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_002', oLine, 'Ending of timing report detected without a beginning detected')
            bStart = False
        if is_start_of_timing_report(oLine):
            bStart = True


def check_beginning_of_timing_report_without_ending(oTimingReportFile):
    oStartLine = None
    for oLine in oTimingReportFile.lines:
        if is_end_of_timing_report(oLine):
            oStartLine = None
        if is_start_of_timing_report(oLine):
            if oStartLine is not None:
                raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_003', oStartLine, 'Beginning of timing report detected without an ending detected')
            oStartLine = oLine
    if oStartLine is not None:
        raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_003', oStartLine, 'Beginning of timing report detected without an ending detected')


def is_start_of_timing_report(oLine):
    return oLine.text.startswith('Slack ')


def is_end_of_timing_report(oLine):
    return oLine.text.strip().startswith('slack ')


def create_timing_report(oTimingReportText):
    oPathTypeLine = extract_path_type_line(oTimingReportText)
    if is_hold_path_type(oPathTypeLine):
        return timing_report.HoldTimingReport(oTimingReportText)
    if is_setup_path_type(oPathTypeLine):
        return timing_report.SetupTimingReport(oTimingReportText)
    raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_005', oPathTypeLine, 'Unknown Path Type in timing report.  Should be either Max or Min')


def is_hold_path_type(oLine):
    return extract_path_type(oLine) == 'hold'


def is_setup_path_type(oLine):
    return extract_path_type(oLine) == 'setup'


def extract_path_type_line(oTimingReportText):
    for oLine in oTimingReportText.lines:
        if has_type(oLine):
            return oLine
    raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_004', oTimingReportText.lines[0], 'No Path Type in timing report')


def populate_timing_report(oTimingReport):
    update_source(oTimingReport)
    update_destination(oTimingReport)
    update_process_corner(oTimingReport)
    update_launch_clock(oTimingReport)
    update_capture_clock(oTimingReport)
    update_launch_clock_path(oTimingReport)
    update_data_path(oTimingReport)
    update_capture_clock_path(oTimingReport)


def update_source(oTimingReport):
    oTimingReport.source = extract_field(oTimingReport, 'Source:', 'vivado_tr_parse_006')


def update_destination(oTimingReport):
    oTimingReport.destination = extract_field(oTimingReport, 'Destination:', 'vivado_tr_parse_007')


def extract_field(oTimingReport, sKey, sErrorId):
    lLines = oTimingReport.get_lines()
    for oLine in lLines:
        if is_key_line(oLine, sKey):
            return extract_key_value(oLine, sKey, sErrorId)
    raise timing_report_parse_error.TimingReportParseError(sErrorId, lLines[0], f'{sKey} was not found in timing report')


def is_key_line(oLine, sKey):
    return oLine.text.strip().startswith(sKey)


def extract_key_value(oLine, sKey, sErrorId):
    lWords = oLine.text.split()
    if len(lWords) < 2:
        raise timing_report_parse_error.TimingReportParseError(sErrorId, oLine, f'{sKey} has no value')
    return lWords[1]


def update_process_corner(oTimingReport):
    oPathTypeLine = extract_path_type_line(oTimingReport.text)
    if 'Fast Process Corner' in oPathTypeLine.text:
        oTimingReport.process_corner = 'Fast'
    elif 'Slow Process Corner' in oPathTypeLine.text:
        oTimingReport.process_corner = 'Slow'
    else:
        raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_008', oPathTypeLine, 'has invalid process corner.  Expecting Fast or Slow.')


def update_launch_clock(oTimingReport):
    oLine = extract_clock_line(oTimingReport, 'Source:')
    oTimingReport.launch_clock = create_clock(oLine)


def update_capture_clock(oTimingReport):
    oLine = extract_clock_line(oTimingReport, 'Destination:')
    oTimingReport.capture_clock = create_clock(oLine)


def create_clock(oLine):
    oClock = timing_report.Clock()
    update_clock_name(oLine, oClock)
    update_clock_period(oLine, oClock)
    return oClock


def update_clock_name(oLine, oClock):
    lWords = oLine.text.split()
    oClock.name = lWords[lWords.index('by') + 1]


def update_clock_period(oLine, oClock):
    lWords = oLine.text.split()
    for sWord in lWords:
        if sWord.startswith('period='):
            oClock.period = extract_period(oLine, sWord)


def extract_period(oLine, sWord):
    sPeriod = remove_parenthesis(sWord)
    sPeriod = remove_curly_braces(sPeriod)
    sPeriod = remove_period_equals(sPeriod)
    sPeriod = remove_ns(oLine, sPeriod)
    check_if_period_is_negative(oLine, sPeriod)
    check_if_period_is_zero(oLine, sPeriod)
    try:
        return float(sPeriod)
    except ValueError:
        raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_010', oLine, 'is missing clock period')


def remove_parenthesis(sWord):
    return sWord.replace(')', '')


def remove_curly_braces(sWord):
    return sWord.replace('}', '')


def remove_period_equals(sWord):
    return sWord.replace('period=', '')


def remove_ns(oLine, sWord):
    if not sWord.endswith('ns'):
        raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_010', oLine, 'incorrect clock period units.  Should be ns.')
    return sWord[:-2]


def check_if_period_is_negative(oLine, sWord):
    if sWord.startswith('-'):
       raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_010', oLine, 'clock period can not be negative.')


def check_if_period_is_zero(oLine, sWord):
    for sChar in sWord:
        if sChar == '0' or sChar == '.':
           continue
        else:
           return
    raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_010', oLine, 'clock period can not be zero.')


def extract_clock_line(oTimingReport, sKey):
    lLines = oTimingReport.get_lines()
    for iOffset, oLine in enumerate(lLines):
        if oLine.text.strip().startswith(sKey):
            if 'clocked by' not in lLines[iOffset + 1].text:
                raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_009', lLines[iOffset + 1], 'is missing clock name information')
            if 'period=' not in lLines[iOffset + 1].text:
                raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_010', lLines[iOffset + 1], 'is missing clock period information')
            return lLines[iOffset + 1]


def extract_launch_clock_path_lines(oTimingReportText):
    return extract_lines_between_separators(oTimingReportText, 1)


def extract_data_path_lines(oTimingReportText):
    return extract_lines_between_separators(oTimingReportText, 2)


def extract_capture_clock_path_lines(oTimingReportText):
    return extract_lines_between_separators(oTimingReportText, 3)


def extract_lines_between_separators(oTimingReportText, iSeparatorStart):
    lLines = []
    iSeparatorCount = 0
    for oLine in oTimingReportText.lines:
        if is_blank_line(oLine):
            continue
        if is_separator_line(oLine):
            iSeparatorCount += 1
            continue
        if iSeparatorCount == iSeparatorStart:
            lLines.append(oLine)
    return lLines


def is_separator_line(oLine):
    return oLine.text.strip().startswith('----')


def is_blank_line(oLine):
    return oLine.text.strip() == ''


def validate_timing_report_text(oTimingReportText):
    check_number_of_separators(oTimingReportText)


def check_number_of_separators(oTimingReportText):
    iSeparatorCount = 0
    for oLine in oTimingReportText.lines:
        if is_separator_line(oLine):
            iSeparatorCount += 1
    if iSeparatorCount != TOTAL_NUMBER_OF_SEPARATORS:
        raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_011', oTimingReportText.lines[0], f'expected {TOTAL_NUMBER_OF_SEPARATORS} separator lines but found {iSeparatorCount}')


def create_delay(oLine):
    if is_net_delay(oLine):
        return create_net_delay(oLine)
    if is_cell_delay(oLine):
        return create_cell_delay(oLine)


def create_cell_delay(oLine):
    lWords = oLine.text.strip().split()
    oDelay = delay_element.CellDelay()
    oDelay.location = lWords[0]
    oDelay.delay_type = lWords[1]
    oDelay.delay = float(lWords[3])
    oDelay.resource = lWords[-1]
    return oDelay


def create_net_delay(oLine):
    lWords = oLine.text.strip().replace(', routed', '').split()
    oDelay = delay_element.NetDelay()
    oDelay.fan_out = int(lWords[1].split('=')[1].replace(')', ''))
    oDelay.delay = float(lWords[2])
    oDelay.resource = lWords[-1]
    return oDelay


def is_delay_row(oLine):
    return is_cell_delay(oLine) or is_net_delay(oLine)


def is_cell_delay(oLine):
    return '(Prop_' in oLine.text


def is_net_delay(oLine):
    return 'net (fo=' in oLine.text


def create_delay_path(lLines):
    oDelayPath = delay_path.DelayPath()
    for oLine in lLines:
        if is_delay_row(oLine):
            oDelayPath.add_delay(create_delay(oLine))
    return oDelayPath


def update_launch_clock_path(oTimingReport):
    lLines = extract_launch_clock_path_lines(oTimingReport.text)
    oTimingReport.launch_clock_path = create_delay_path(lLines)
    

def update_data_path(oTimingReport):
    lLines = extract_data_path_lines(oTimingReport.text)
    oTimingReport.data_path = create_delay_path(lLines)
    

def update_capture_clock_path(oTimingReport):
    lLines = extract_capture_clock_path_lines(oTimingReport.text)
    oTimingReport.capture_clock_path = create_delay_path(lLines)
    

def has_type(oLine):
    if 'Path Type:' in oLine.text:
        return True
    return False


def extract_path_type(oLine):
    lWords = oLine.text.split()
    if len(lWords) < 3:
        return None
    if lWords[2] == 'Max':
        return 'setup'
    if lWords[2] == 'Min':
        return 'hold'
    return None


def add_output_delay(line, data_struct):
    if is_output_delay(line):
        data_struct['output_delay'] = extract_output_delay(line)
        return True
    return False


def is_output_delay(line):
    if 'Output Delay:' in line:
        return True
    return False


def extract_output_delay(line):
    temp_list = line.split(':')
    return float(temp_list[1][:-2])


def add_launch_edge(line, data_struct, flag):
    if is_launch_clock_edge(line, flag):
        data_struct['launch_edge'] = extract_clock_edge(line)
        return True
    return False


def add_capture_edge(line, data_struct, flag):
    if is_capture_clock_edge(line, flag):
        data_struct['capture_edge'] = extract_clock_edge(line)
        return True
    return False


def is_launch_clock_edge(line, flag):
    if is_clock_edge(line) and not flag:
        return True
    return False


def is_capture_clock_edge(line, flag):
    if is_clock_edge(line) and flag:
        return True
    return False


def is_clock_edge(line):
    if '(clock ' in line and ' edge)' in line:
        return True
    return False


def extract_clock_edge(line):
    temp_list = line.split(')')
    temp_list = temp_list[1].split()
    return float(temp_list[0])


def build_net_delay_struct(line, data_struct):
    delay = {}
    delay['type'] = 'net'
    delay['delay'] = extract_net_delay(line)
    delay['resource'] = extract_resource(line)
    delay['fan_out'] = extract_fanout(line)
    return delay


def extract_net_delay(line):
    temp_list = line.split(')')
    delay_list = temp_list[1].split()
    return float(delay_list[0])


def extract_resource(line):
    temp_list = line.split()
    return temp_list[-1]


def extract_fanout(line):
    temp_list = line.split(')')
    fanout_list = temp_list[0].split('(')
    fanout_list = fanout_list[1].split(',')
    fanout_list = fanout_list[0].split('=')
    return int(fanout_list[1])


def add_cell_delay(line, data_struct, found_launch_edge):
    delay = build_cell_delay_struct(line, data_struct)
    if found_launch_edge:
        data_struct['data_path'].append(delay)
    else:
        data_struct['required_path'].append(delay)


def build_cell_delay_struct(line, data_struct):
    delay = {}
    delay['type'] = 'cell'
    delay['location'] = extract_location(line)
    delay['delay_type'] = extract_delay_type(line)
    delay['delay'] = extract_cell_delay(line)
    delay['resource'] = extract_resource(line)
    return delay


def extract_location(line):
    temp_list = line.split()
    return temp_list[0]


def extract_delay_type(line):
    temp_list = line.split()
    return temp_list[1]


def extract_cell_delay(line):
    temp_list = line.split()
    return float(temp_list[3])
