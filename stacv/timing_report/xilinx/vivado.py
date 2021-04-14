
def parse_timing_report(report):
    reports = []
    data_struct = create_data_struct()
    found_paths = False
    found_launch_edge = False
    for line in report:
        found_paths = is_this_the_start_of_the_timing_paths(line, found_paths)
        if not found_paths:
            if add_type(line, data_struct):
                continue
            if add_output_delay(line, data_struct):
                continue
            continue
        if is_end_of_report(line):
            reports.append(data_struct)
            data_struct = create_data_struct()
            found_paths = False
            found_launch_edge = False
            continue
        if add_launch_edge(line, data_struct, found_launch_edge):
            found_launch_edge = True
            continue
        if add_capture_edge(line, data_struct, found_launch_edge):
            found_launch_edge = False
            continue
        if add_net_delay(line, data_struct, found_launch_edge):
            continue
        if ignore_line(line):
            continue
        add_cell_delay(line, data_struct, found_launch_edge)
    return reports


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


def extract_path_type(line):
    if 'Max' in line:
        return 'setup'
    elif 'Min' in line:
        return 'hold'


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
