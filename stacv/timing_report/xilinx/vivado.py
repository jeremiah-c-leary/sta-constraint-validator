
def parse_timing_report(report):
    reports = []
    data_struct = create_data_struct()
    found_paths = False
    found_launch_edge = False
    for line in report:
        if 'Location' in line and 'Delay type' in line:
            found_paths = True
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
    if 'Path Type:' in line:
        if 'Max' in line:
            data_struct['type'] = 'setup'
        elif 'Min' in line:
            data_struct['type'] = 'hold'

        temp_list = line.split(':')
        temp_list = temp_list[1].split('at')
        data_struct['process_corner'] = temp_list[1].strip()
        return True
    return False


def add_output_delay(line, data_struct):
    if 'Output Delay:' in line:
        temp_list = line.split(':')
        data_struct['output_delay'] = float(temp_list[1][:-2])
        return True
    return False


def add_launch_edge(line, data_struct, flag):
    if '(clock ' in line and ' edge)' in line and not flag:
        temp_list = line.split(')')
        temp_list = temp_list[1].split()
        data_struct['launch_edge'] = float(temp_list[0])
        return True
    return False

        
def add_capture_edge(line, data_struct, flag):
    if '(clock ' in line and ' edge)' in line and flag:
        temp_list = line.split(')')
        temp_list = temp_list[1].split()
        data_struct['capture_edge'] = float(temp_list[0])
        return True
    return False


def add_net_delay(line, data_struct, found_launch_edge):
    if 'net (fo=' in line:
        delay = {}
        delay['type'] = 'net'
        temp_list = line.split(')')
        delay_list = temp_list[1].split()
        delay['delay'] = float(delay_list[0])
        delay['resource'] = delay_list[2]
        fanout_list = temp_list[0].split('(')
        fanout_list = fanout_list[1].split(',')
        fanout_list = fanout_list[0].split('=')
        delay['fan_out'] = int(fanout_list[1])
        if found_launch_edge:
            data_struct['data_path'].append(delay)
        else:
            data_struct['required_path'].append(delay)
        return True
    return False


def add_cell_delay(line, data_struct, found_launch_edge):
    delay = {}
    delay['type'] = 'cell'
    temp_list = line.split()
    delay['location'] = temp_list[0]
    delay['delay_type'] = temp_list[1]
    delay['delay'] = float(temp_list[3])
    delay['resource'] = temp_list[-1]
    if found_launch_edge:
        data_struct['data_path'].append(delay)
    else:
        data_struct['required_path'].append(delay)
