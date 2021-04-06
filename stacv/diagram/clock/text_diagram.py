
from stacv import clock


def render(timing_model, pin):

    diagram = []

    device_pin = timing_model.get_device_pin(pin)
    launch_pin = timing_model.get_device_clock_named(device_pin.launch_clock)
    capture_pin = timing_model.get_device_pin('O_DAC_SCLK')
    launch_clock = clock.new(launch_pin.max_freq)
    capture_clock = clock.new(capture_pin.max_freq)
    if launch_clock.period < capture_clock.period:
        clock.expand(capture_clock, 2)
        clock.expand(launch_clock, 10)
    dwell_time = 2

    line = '   '
    for edge in launch_clock.edges[:-1]:
       if edge.direction == 'rising':
           line += '__ ' 
       else:
           line += '   '
    diagram.append(line)

    line = '__'
    for edge in launch_clock.edges[:-1]:
       if edge.direction == 'rising':
           line += '|  '
       else:
           line += '|__'
    line += '|'

    diagram.append(line)

    line = ''
    diagram.append(line)

    line = '   '
    for edge in capture_clock.edges[:-1]:
        if edge.direction == 'rising':
            line += '_'*(dwell_time*3 + dwell_time*2 + 4) + ' '
        else:
            line += ' '*(dwell_time*3 + dwell_time*2 + 4) + ' '
    diagram.append(line)

    line = '__'
    for edge in capture_clock.edges[:-1]:
        if edge.direction == 'rising':
            line += '|' + ' '*(dwell_time*3 + dwell_time*2 + 4)
        else:
            line += '|' + '_'*(dwell_time*3 + dwell_time*2 + 4)
    line += '|'
    diagram.append(line)

    return diagram


def extract_data_format(data_struct):
    data_format = {}
    data_format['device_width'] = extract_device_width(data_struct)
    data_format['trace_width'] = extract_trace_width(data_struct)
    data_format['part_width'] = extract_part_width(data_struct)
    return data_format


def extract_device_width(data_struct):
    '''
    2*space + length of device name + 2*space
    or
    2*space + length_of_port + space + [
    '''
    device_width = 2 + len(data_struct['device']['name']) + 2
    for my_trace in data_struct['traces']:
        port_width = 2 + len(my_trace['device_pin']) + 1 + 1
        device_width = max(device_width, port_width)
    return device_width


def extract_trace_width(data_struct):
    '''
    1 + 4 + 1 + length of trace name + 1 + 4 + 1
    '''
    trace_width = 0
    for my_trace in data_struct['traces']:
        trace_width = max(trace_width, 1 + 4 + 1 + len(my_trace['name']) + 1 + 4 + 1)
    return trace_width


def extract_part_width(data_struct):
    '''
    2*space + length of part name + 2*space
    or
    ] + space + length_of_pin_name + 2*space
    '''
    part_width = 2 + len(data_struct['part']['name']) + 2
    for my_trace in data_struct['traces']:
        port_width = 1 + 1 + len(my_trace['part_pin']) + 2
        part_width = max(part_width, port_width)
    return part_width


def build_top_line(data_format):
    line = ''
    line += '-'*data_format['device_width']
    line += '+'
    line += ' '*data_format['trace_width']
    line += '+'
    line += '-'*data_format['part_width']
    return line


def build_device_and_part_names(data_format, data_struct):
    device_name = data_struct['device']['name']
    device_width = data_format['device_width']
    part_name = data_struct['part']['name']
    part_width = data_format['part_width']

    line = f'{device_name:^{device_width}}'
    line += '|' + ' '*data_format['trace_width'] + '|'
    line += f'{part_name:^{part_width}}'

    return line


def build_empty_line(data_format):
    line = ''
    line += ' '*data_format['device_width']
    line += '|'
    line += ' '*data_format['trace_width']
    line += '|'
    return line


def build_trace_line(data_format, trace_struct):

    line = ' '*(data_format['device_width'] - 2 - len(trace_struct['device_pin']))
    line += trace_struct['device_pin']
    line += ' [ ]'
    if trace_struct['direction'] == 'right':
        trace = '-'*(data_format['trace_width'] - 2 - 1) + '>'
    elif trace_struct['direction'] == 'left':
        trace = '<' + '-'*(data_format['trace_width'] - 2 - 1)
    left_trace_point = int((data_format['trace_width'] - 2)/2 - (len(trace_struct['name']) + 2)/2)
    right_trace_point = int((data_format['trace_width'] - 2)/2 + (len(trace_struct['name']) + 2)/2)
    trace = trace[:left_trace_point] + ' ' + trace_struct['name'] + ' ' + trace[right_trace_point:]

    line += trace

    line += '[ ] '
    line += trace_struct['part_pin']

    return line
