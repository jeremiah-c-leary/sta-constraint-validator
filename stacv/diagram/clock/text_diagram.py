
from stacv import clock


def render(timing_model, pin):

    diagram = []

    launch_clock, capture_clock = build_clocks(timing_model, pin)

    launch_dwell_time, capture_dwell_time = calculate_dwell_times(launch_clock, capture_clock)

    diagram.extend(render_clock(launch_clock, launch_dwell_time))
    diagram.extend(render_blank_line())
    diagram.extend(render_setup_arc(launch_clock, launch_dwell_time, capture_clock, capture_dwell_time))
    diagram.extend(render_hold_arc(launch_clock, launch_dwell_time, capture_clock, capture_dwell_time))
    diagram.extend(render_blank_line())
    diagram.extend(render_clock(capture_clock, capture_dwell_time, letter=True))

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


def render_clock(launch_clock, dwell_time, letter=False):
    lines = []


    if not letter:
        if len(launch_clock.edges) > 10:
            line = '   '
            for edge_number, edge in enumerate(launch_clock.edges[:-1]):
               edge_number = int((edge_number + 2) / 10)
               if edge_number > 0:
                   line += ' '*dwell_time + str(edge_number)
               else:
                   line += ' '*dwell_time + ' '
            lines.append(line)

        line = '  1'
        for edge_number, edge in enumerate(launch_clock.edges[:-1]):
           if edge.direction == 'rising':
               line += '_'*dwell_time + str((edge_number + 2)%10)
           else:
               line += ' '*dwell_time + str((edge_number + 2)%10)
        lines.append(line)
    else:
        line = '  a'
        for edge_number, edge in enumerate(launch_clock.edges[:-1]):
           if edge.direction == 'rising':
               line += '_'*dwell_time + str(conv_number_to_letter(edge_number + 2))
           else:
               line += ' '*dwell_time + str(conv_number_to_letter(edge_number + 2))
        lines.append(line)

    line = '__'
    for edge in launch_clock.edges[:-1]:
       if edge.direction == 'rising':
           line += '|' + ' '*dwell_time
       else:
           line += '|' + '_'*dwell_time
    line += '|'

    lines.append(line)

    return lines


def render_blank_line():
    return ['']


def calculate_dwell_times(launch_clock, capture_clock):
    if launch_clock.period < capture_clock.period:
        launch_dwell_time, capture_dwell_time = calculate_fast_and_slow_dwell_times(launch_clock, capture_clock)
    else:
        capture_dwell_time, launch_dwell_time = calculate_fast_and_slow_dwell_times(capture_clock, launch_clock)
    return launch_dwell_time, capture_dwell_time


def calculate_fast_and_slow_dwell_times(fast_clock, slow_clock):
    fast_dwell_time = 2

    ratio = int(slow_clock.period/fast_clock.period)

    number_of_fast_edges_in_half_slow_period = int(ratio) - 1
    slow_dwell_time = ratio*fast_dwell_time + number_of_fast_edges_in_half_slow_period
    return fast_dwell_time, slow_dwell_time


def render_setup_arc(launch_clock, launch_dwell_time, capture_clock, capture_dwell_time):
    lines = []

    capture_edge = conv_letter_to_number(capture_clock.setup_edge)

    launch_edge_index = (launch_dwell_time + 1) * (launch_clock.edge - 1) + 3- 1
    capture_edge_index = (capture_dwell_time + 1) * (capture_edge - 1) + 3 - 1
    delta = capture_edge_index - launch_edge_index - 2
    
    line = ' '*launch_edge_index + '|' + '-'*delta + '>|'

    lines.append(line)

    return lines


def render_hold_arc(launch_clock, launch_dwell_time, capture_clock, capture_dwell_time):
    lines = []

    capture_edge = conv_letter_to_number(capture_clock.hold_edge)

    launch_edge_index = (launch_dwell_time + 1) * (launch_clock.edge - 1) + 3- 1
    capture_edge_index = (capture_dwell_time + 1) * (capture_edge - 1) + 3 - 1
    delta = launch_edge_index - capture_edge_index - 2
    
    line = ' '*capture_edge_index + '|<' + '-'*delta + '|'
    lines.append(line)

    return lines


letter_mapping_table = [None, 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']


def conv_letter_to_number(letter):
    return letter_mapping_table.index(letter)


def conv_number_to_letter(number):
    return letter_mapping_table[number]
