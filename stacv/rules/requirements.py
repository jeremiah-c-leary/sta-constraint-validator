'''
Contains functions to calculate the setup and hold requirements between the configured edges.
'''

from stacv.rules import edge_times


def calculate_configuration_setup_requirement(oPort):
    fCaptureEdgeTime = edge_times.calculate_edge_time(oPort.capture_clock.period, oPort.capture_clock.setup_edge)
    fLaunchEdgeTime = edge_times.calculate_edge_time(oPort.launch_clock.period, oPort.launch_clock.setup_edge)
    return fCaptureEdgeTime - fLaunchEdgeTime


def calculate_configuration_hold_requirement(oPort):
    fCaptureEdgeTime = edge_times.calculate_edge_time(oPort.capture_clock.period, oPort.capture_clock.hold_edge)
    fLaunchEdgeTime = edge_times.calculate_edge_time(oPort.launch_clock.period, oPort.launch_clock.hold_edge)
    return fCaptureEdgeTime - fLaunchEdgeTime
