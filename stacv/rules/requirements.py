'''
Contains functions to calculate the setup and hold requirements between the configured edges.

The requirements include each clock's phase, as the timing tool reports them.
The edge requirements leave the phase out: the multicycle paths count whole edges, and the phase moves an edge within one.
'''

from stacv.rules import edge_times


def calculate_configuration_setup_requirement(oPort):
    return calculate_edge_setup_requirement(oPort) + calculate_phase_difference(oPort)


def calculate_configuration_hold_requirement(oPort):
    return calculate_edge_hold_requirement(oPort) + calculate_phase_difference(oPort)


def calculate_edge_setup_requirement(oPort):
    iCaptureEdgeNumber = edge_times.convert_edge_letter_to_number(oPort.capture_clock.setup_edge)
    fCaptureEdgeTime = edge_times.calculate_edge_time(oPort.capture_clock.period, iCaptureEdgeNumber)
    fLaunchEdgeTime = edge_times.calculate_edge_time(oPort.launch_clock.period, oPort.launch_clock.setup_edge)
    return fCaptureEdgeTime - fLaunchEdgeTime


def calculate_edge_hold_requirement(oPort):
    iCaptureEdgeNumber = edge_times.convert_edge_letter_to_number(oPort.capture_clock.hold_edge)
    fCaptureEdgeTime = edge_times.calculate_edge_time(oPort.capture_clock.period, iCaptureEdgeNumber)
    fLaunchEdgeTime = edge_times.calculate_edge_time(oPort.launch_clock.period, oPort.launch_clock.hold_edge)
    return fCaptureEdgeTime - fLaunchEdgeTime


def calculate_phase_difference(oPort):
    return oPort.capture_clock.phase - oPort.launch_clock.phase
