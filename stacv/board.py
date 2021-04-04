
from . import trace


def new(board_config):

    board = Board()

    for trace_name in board_config['board']['trace']:

        trace_args = extract_trace_data(trace_name, board_config)

        new_trace = trace.New(*trace_args)

        board.add_trace(new_trace)

    return board


def extract_trace_data(trace_name, board_config):
    trace_config = board_config['board']['trace'][trace_name]
    device_pin = trace_config['device_pin']
    part_pin = trace_config['part_pin']
    delay_max = trace_config['delay']['max']
    delay_min = trace_config['delay']['min']
    return trace_name, device_pin, part_pin, delay_max, delay_min


class Board():

    def __init__(self):
        self.traces = []

    def add_trace(self, trace):
        self.traces.append(trace)
   
