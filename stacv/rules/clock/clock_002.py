
from stacv.intent import clock


def check(timing_report, timing_model):
    '''
    Purpose:  This rule checks the launching edge is correct.
    '''
    tr_path_edge = timing_report.launch_edge
    tm_launch_time = calculate_launch_edge(timing_report, timing_model)

    if tr_path_edge == tm_launch_time:
        return True
    return False 


def calculate_launch_edge(timing_report, timing_model):
    end_point = timing_model.get_device_pin(timing_report.data_path.delays[-1].resource)
    path_edge = end_point.launch_edge
    launch_clock = timing_model.get_device_clock_named(end_point.launch_clock) 
    launch_time = calculate_edge_time(launch_clock, path_edge)
    return launch_time


def calculate_edge_time(launch_clock, path_edge):
    launch_clock = clock.new(launch_clock.frequency)
    clock.expand(launch_clock, path_edge)
    return launch_clock.edges[path_edge - 1].time
