
from stacv import pin


def extract_data_structure(timing_model):

    diagram = {}
    diagram['device'] = extract_device_name(timing_model)
    diagram['part'] = extract_part_name(timing_model)
    diagram['traces'] = extract_traces(timing_model)

    return diagram


def extract_device_name(timing_model):

    device = {}

    device['name'] = timing_model.device_name

    return device


def extract_part_name(timing_model):

    part = {}

    part['name'] = timing_model.part_name

    return part


def extract_traces(timing_model):

    traces = []

    traces.extend(extract_input_traces(timing_model))
    traces.extend(extract_output_traces(timing_model))
    traces.extend(extract_clock_traces(timing_model))

    return traces


def extract_input_traces(timing_model):

    traces = []

    input_device_pins = extract_input_pins(timing_model)

    for input_pin in input_device_pins:
        trace = {}
        trace['name'] = timing_model.traces.get_trace_name_connected_to_device_pin(input_pin.name)
        trace['clock'] = False
        trace['device_pin'] = input_pin.name
        trace['part_pin'] = timing_model.traces.get_part_pin_name_connected_to(input_pin.name)
        trace['direction'] = 'left'
        traces.append(trace)

    return traces


def extract_input_pins(timing_model):
    input_device_pins = []
    for device_pin in timing_model.device_interface.data_pins:
        if isinstance(device_pin, pin.DeviceInputPin):
            input_device_pins.append(device_pin)
    return input_device_pins


def extract_output_traces(timing_model):

    traces = []

    output_device_pins = extract_output_pins(timing_model)

    for output_pin in output_device_pins:
        trace = {}
        trace['name'] = timing_model.traces.get_trace_name_connected_to_device_pin(output_pin.name)
        trace['clock'] = False
        trace['device_pin'] = output_pin.name
        trace['part_pin'] = timing_model.traces.get_part_pin_name_connected_to(output_pin.name)
        trace['direction'] = 'right'
        traces.append(trace)

    return traces


def extract_output_pins(timing_model):
    output_device_pins = []
    for device_pin in timing_model.device_interface.data_pins:
        if isinstance(device_pin, pin.DeviceOutputPin):
            output_device_pins.append(device_pin)
    return output_device_pins


def extract_clock_traces(timing_model):

    clock_device_pin = timing_model.device_interface.external_clock

    traces = []

    trace = {}
    trace['name'] = timing_model.traces.get_trace_name_connected_to_device_pin(clock_device_pin.name)
    trace['clock'] = True
    trace['device_pin'] = clock_device_pin.name
    trace['part_pin'] = timing_model.traces.get_part_pin_name_connected_to(clock_device_pin.name)
    trace['direction'] = 'right'
    traces.append(trace)

    return traces


def render_text_diagram(timing_model):

    data_struct = extract_data_structure(timing_model)

    data_format = extract_data_format(data_struct)

    diagram = []
    diagram.append(render_top_line(data_format))
    diagram.append(render_device_and_part_names(data_format, data_struct))
    diagram.append(render_empty_line(data_format))
    for my_trace in data_struct['traces']:
        diagram.append(render_trace_line(data_format, my_trace))
        diagram.append(render_empty_line(data_format))
    diagram.append(render_top_line(data_format))

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


def render_top_line(data_format):
    line = ''
    line += '-'*data_format['device_width']
    line += '+'
    line += ' '*data_format['trace_width']
    line += '+'
    line += '-'*data_format['part_width']
    return line


def render_device_and_part_names(data_format, data_struct):
    device_name = data_struct['device']['name']
    device_width = data_format['device_width']
    part_name = data_struct['part']['name']
    part_width = data_format['part_width']

    line = f'{device_name:^{device_width}}'
    line += '|' + ' '*data_format['trace_width'] + '|'
    line += f'{part_name:^{part_width}}'
    

    return line


def render_empty_line(data_format):
    line = ''
    line += ' '*data_format['device_width']
    line += '|'
    line += ' '*data_format['trace_width']
    line += '|'
    return line


def render_trace_line(data_format, trace_struct):

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
