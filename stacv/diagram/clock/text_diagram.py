
from stacv import clock
from stacv import utils


def render(timing_model, pin):

    diagram = []

    launch_clock, capture_clock = build_clocks(timing_model, pin)

    diagram.extend(render_clock(launch_clock))
    diagram.extend(render_blank_line())
    diagram.extend(render_setup_arc(launch_clock, capture_clock))
    diagram.extend(render_hold_arc(launch_clock, capture_clock))
    diagram.extend(render_blank_line())
    diagram.extend(render_clock(capture_clock, letter=True))

    return diagram


def build_clocks(timing_model, pin):
    device_data_pin = timing_model.get_device_pin(pin)
    launch_clock_pin = timing_model.get_device_clock_named(device_data_pin.launch_clock)
    capture_clock_pin = timing_model.get_device_clock_named(device_data_pin.capture_clock)

    launch_clock = clock.new(launch_clock_pin.frequency)
    launch_clock.edge = device_data_pin.launch_edge

    capture_clock = clock.new(capture_clock_pin.frequency)
    capture_clock.setup_edge = device_data_pin.setup_edge
    capture_clock.hold_edge = device_data_pin.hold_edge

    calculate_dwell_times(launch_clock, capture_clock)

    expand_clocks(launch_clock, capture_clock)

    return launch_clock, capture_clock


def expand_clocks(launch_clock, capture_clock):
    slow_clock_expansion = 2
    if launch_clock.period < capture_clock.period:
        clock.expand(capture_clock, slow_clock_expansion)
        fast_clock_expansion = slow_clock_expansion * int(capture_clock.period/launch_clock.period)
        clock.expand(launch_clock, fast_clock_expansion)
    else:
        clock.expand(launch_clock, slow_clock_expansion)
        fast_clock_expansion = slow_clock_expansion * int(launch_clock.period/capture_clock.period)
        clock.expand(capture_clock, fast_clock_expansion)


def render_clock(launch_clock, letter=False):
    lines = []

    lines.extend(render_edge_ids(launch_clock, letter))
    lines.append(render_clock_edges(launch_clock))

    return lines


def render_edge_ids(launch_clock, letter):
    lines = []
    if not letter:
        render_number_line(launch_clock, lines)
    else:
        render_letter_line(launch_clock, lines)
    return lines


def render_number_line(launch_clock, lines):
    render_tens_line(launch_clock, lines)
    render_ones_line(launch_clock, lines)


def render_letter_line(launch_clock, lines):
    line = '  a'
    for edge_number, edge in enumerate(launch_clock.edges[:-1]):
       if edge.direction == 'rising':
           line += '_'*launch_clock.dwell_time + str(utils.conv_number_to_letter(edge_number + 2))
       else:
           line += ' '*launch_clock.dwell_time + str(utils.conv_number_to_letter(edge_number + 2))
    lines.append(line)


def render_ones_line(launch_clock, lines):
    line = '  1'
    for edge_number, edge in enumerate(launch_clock.edges[:-1]):
       if edge.direction == 'rising':
           line += '_'*launch_clock.dwell_time + str((edge_number + 2)%10)
       else:
           line += ' '*launch_clock.dwell_time + str((edge_number + 2)%10)
    lines.append(line)


def render_tens_line(launch_clock, lines):
    if len(launch_clock.edges) > 10:
        line = '   '
        for edge_number, edge in enumerate(launch_clock.edges[:-1]):
           edge_number = int((edge_number + 2) / 10)
           if edge_number > 0:
               line += ' '*launch_clock.dwell_time + str(edge_number)
           else:
               line += ' '*launch_clock.dwell_time + ' '
        lines.append(line)


def render_clock_edges(launch_clock):
    line = '__'
    for edge in launch_clock.edges[:-1]:
       line = render_rising_clock_edge(edge, launch_clock, line)
       line = render_falling_clock_edge(edge, launch_clock, line)
    line += '|'
    return line


def render_rising_clock_edge(edge, launch_clock, line):
       if edge.direction == 'rising':
           line += '|' + ' '*launch_clock.dwell_time
       return line


def render_falling_clock_edge(edge, launch_clock, line):
       if edge.direction == 'falling':
           line += '|' + '_'*launch_clock.dwell_time
       return line


def render_blank_line():
    return ['']


def calculate_dwell_times(launch_clock, capture_clock):
    if launch_clock.period < capture_clock.period:
        launch_clock.dwell_time, capture_clock.dwell_time = calculate_fast_and_slow_dwell_times(launch_clock, capture_clock)
    else:
        capture_clock.dwell_time, launch_clock.dwell_time = calculate_fast_and_slow_dwell_times(capture_clock, launch_clock)


def calculate_fast_and_slow_dwell_times(fast_clock, slow_clock, fast_dwell_time=2):

    ratio = int(slow_clock.period/fast_clock.period)

    number_of_fast_edges_in_half_slow_period = int(ratio) - 1
    slow_dwell_time = ratio*fast_dwell_time + number_of_fast_edges_in_half_slow_period
    return fast_dwell_time, slow_dwell_time


def render_setup_arc(launch_clock, capture_clock):
    lines = []

    capture_edge = utils.conv_letter_to_number(capture_clock.setup_edge)

    launch_edge_index = (launch_clock.dwell_time + 1) * (launch_clock.edge - 1) + 3- 1
    capture_edge_index = (capture_clock.dwell_time + 1) * (capture_edge - 1) + 3 - 1
    delta = capture_edge_index - launch_edge_index - 2
    
    line = ' '*launch_edge_index + '|' + '-'*delta + '>|'

    lines.append(line)

    return lines


def render_hold_arc(launch_clock, capture_clock):
    lines = []

    capture_edge = utils.conv_letter_to_number(capture_clock.hold_edge)

    launch_edge_index = (launch_clock.dwell_time + 1) * (launch_clock.edge - 1) + 3- 1
    capture_edge_index = (capture_clock.dwell_time + 1) * (capture_edge - 1) + 3 - 1
    delta = launch_edge_index - capture_edge_index - 2
    
    line = ' '*capture_edge_index + '|<' + '-'*delta + '|'
    lines.append(line)

    return lines
