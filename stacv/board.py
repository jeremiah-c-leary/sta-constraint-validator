
from . import trace


def new(board_config):

    board = Board()

    for trace_config in board_config['board']['trace']:

        new_trace = trace.New(trace_config)

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
   
    def get_part_pin_name_connected_to(self, name):
        for my_trace in self.traces:
            if my_trace.device_pin == name:
                return my_trace.part_pin
        return None
