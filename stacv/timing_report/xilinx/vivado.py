
from stacv.timing_report import timing_report
from stacv.timing_report import timing_report_file
from stacv.timing_report import timing_report_list
from stacv.timing_report import timing_report_parse_error


def parse_timing_report(oTimingReportFile):
    validate_timing_report_file(oTimingReportFile)
    oTimingReports = timing_report_list.TimingReportList()
    for oTimingReportText in extract_timing_report_texts(oTimingReportFile):
        oTimingReport = create_timing_report(oTimingReportText)
        populate_timing_report(oTimingReport)
        oTimingReports.add(oTimingReport)
    return oTimingReports


def extract_timing_report_texts(oTimingReportFile):
    lTimingReports = []
    lReport = None
    iStartLineNumber = 0
    for iLine, sLine in enumerate(oTimingReportFile.lines, start=1):
        if is_start_of_timing_report(sLine):
            lReport = []
            iStartLineNumber = iLine
        if lReport is None:
            continue
        lReport.append(sLine)
        if is_end_of_timing_report(sLine):
            oTimingReportText = timing_report_file.TimingReportText(oTimingReportFile, iStartLineNumber, lReport)
            lTimingReports.append(oTimingReportText)
            lReport = None

    return lTimingReports


def validate_timing_report_file(oTimingReportFile):
    check_timing_reports_exist(oTimingReportFile)
    check_ending_of_timing_report_without_beginning(oTimingReportFile)
    check_beginning_of_timing_report_without_ending(oTimingReportFile)


def check_timing_reports_exist(oTimingReportFile):
    bStart = False
    for sLine in oTimingReportFile.lines:
        if is_start_of_timing_report(sLine):
            bStart = True
            break

    if not bStart:
        raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_001', oTimingReportFile.filename, 1, 'No timing reports detected')


def check_ending_of_timing_report_without_beginning(oTimingReportFile):
    bStart = False
    for iLine, sLine in enumerate(oTimingReportFile.lines, start=1):
        if is_end_of_timing_report(sLine):
            if not bStart:
                raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_002', oTimingReportFile.filename, iLine, 'Ending of timing report detected without a beginning detected')
            bStart = False
        if is_start_of_timing_report(sLine):
            bStart = True


def check_beginning_of_timing_report_without_ending(oTimingReportFile):
    bStart = False
    iStartLineNumber = 0
    for iLine, sLine in enumerate(oTimingReportFile.lines, start=1):
        if is_end_of_timing_report(sLine):
            bStart = False
        if is_start_of_timing_report(sLine):
            if bStart:
                raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_003', oTimingReportFile.filename, iStartLineNumber, 'Beginning of timing report detected without an ending detected')
            bStart = True
            iStartLineNumber = iLine
    if bStart:
        raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_003', oTimingReportFile.filename, iStartLineNumber, 'Beginning of timing report detected without an ending detected')


def is_start_of_timing_report(sLine):
    return sLine.startswith('Slack ')


def is_end_of_timing_report(sLine):
    return sLine.strip().startswith('slack ')


def create_timing_report(oTimingReportText):
    iPathTypeOffset, sPathTypeLine = extract_path_type_line(oTimingReportText)
    if is_hold_path_type(sPathTypeLine):
        return timing_report.HoldTimingReport(oTimingReportText)
    if is_setup_path_type(sPathTypeLine):
        return timing_report.SetupTimingReport(oTimingReportText)
    raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_005', oTimingReportText.get_filename(), oTimingReportText.line_number_of(iPathTypeOffset), 'Unknown Path Type in timing report.  Should be either Max or Min')


def is_hold_path_type(sLine):
    return extract_path_type(sLine) == 'hold'


def is_setup_path_type(sLine):
    return extract_path_type(sLine) == 'setup'


def extract_path_type_line(oTimingReportText):
    for iOffset, sLine in enumerate(oTimingReportText.lines):
        if has_type(sLine):
            return iOffset, sLine
    raise timing_report_parse_error.TimingReportParseError('vivado_tr_parse_004', oTimingReportText.get_filename(), oTimingReportText.line_number_of(), 'No Path Type in timing report')


def populate_timing_report(oTimingReport):
    update_source(oTimingReport)
    update_destination(oTimingReport)


def update_source(oTimingReport):
    oTimingReport.source = extract_field(oTimingReport, 'Source:', 'vivado_tr_parse_006')


def update_destination(oTimingReport):
    oTimingReport.destination = extract_field(oTimingReport, 'Destination:', 'vivado_tr_parse_007')


def extract_field(oTimingReport, sKey, sErrorId):
    for iOffset, sLine in enumerate(oTimingReport.get_lines()):
        if is_key_line(sLine, sKey):
            return extract_key_value(sLine, iOffset, oTimingReport, sKey, sErrorId)
    raise timing_report_parse_error.TimingReportParseError(sErrorId, oTimingReport.get_filename(), oTimingReport.line_number_of(), f'{sKey} was not found in timing report')


def is_key_line(sLine, sKey):
    return sLine.strip().startswith(sKey)


def extract_key_value(sLine, iOffset, oTimingReport, sKey, sErrorId):
    lWords = sLine.split()
    if len(lWords) < 2:
        raise timing_report_parse_error.TimingReportParseError(sErrorId, oTimingReport.get_filename(), oTimingReport.line_number_of(iOffset), f'{sKey} has not value')
    return lWords[1]


#    for line in report:
#        found_paths = is_this_the_start_of_the_timing_paths(line, found_paths)
#        if not found_paths:
#            if add_type(line, data_struct):
#                continue
#            if add_output_delay(line, data_struct):
#                continue
#            continue
#        if is_end_of_report(line):
#            reports.append(data_struct)
#            data_struct = create_data_struct()
#            found_paths = False
#            found_launch_edge = False
#            continue
#        if add_launch_edge(line, data_struct, found_launch_edge):
#            found_launch_edge = True
#            continue
#        if add_capture_edge(line, data_struct, found_launch_edge):
#            found_launch_edge = False
#            continue
#        if add_net_delay(line, data_struct, found_launch_edge):
#            continue
#        if ignore_line(line):
#            continue
#        add_cell_delay(line, data_struct, found_launch_edge)
#    return oTimingReports


def is_this_the_start_of_the_timing_paths(line, found_paths):
    if 'Location' in line and 'Delay type' in line:
        return True
    return found_paths


def create_data_struct():
    data_struct = {}
    data_struct['data_path'] = []
    data_struct['required_path'] = []
    return data_struct


def is_end_of_report(line):
    if ' slack ' in line:
        return True
    return False


def ignore_line(line):
    if line == '':
        return True
    if line.startswith('  ---'):
        return True
    if line.endswith(')'):
        return True
    if 'clock pessimism' in line:
        return True
    if 'clock uncertainty' in line:
        return True
    if 'output delay' in line:
        return True
    if 'required time' in line:
        return True
    if 'arrival time' in line:
        return True
    if '(' not in line:
        return True
    return False


def add_type(line, data_struct):
    if has_type(line):
        data_struct['type'] = extract_path_type(line)
        data_struct['process_corner'] = extract_process_corner(line)
        return True
    return False


def has_type(line):
    if 'Path Type:' in line:
        return True
    return False


def extract_path_type(sLine):
    lWords = sLine.split()
    if len(lWords) < 3:
        return None
    if lWords[2] == 'Max':
        return 'setup'
    if lWords[2] == 'Min':
        return 'hold'
    return None


def extract_process_corner(line):
    temp_list = line.split(':')
    temp_list = temp_list[1].split('at')
    return temp_list[1].strip()


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


def add_net_delay(line, data_struct, found_launch_edge):
    if not is_net_delay(line):
        return False

    delay = build_net_delay_struct(line, data_struct)
    if found_launch_edge:
        data_struct['data_path'].append(delay)
    else:
        data_struct['required_path'].append(delay)
    return True


def is_net_delay(line):
    if 'net (fo=' in line:
        return True
    return False


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
