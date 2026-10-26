'''
Generates Vivado timing constraints for the ports of an interface.
'''

from stacv.inputs import port_profile
from stacv.rules import edge_times
from stacv.rules import output_delays


def generate_constraints(oInterface, oTraceList, oPart):
    lLines = []
    lLines.extend(generate_clocks(oInterface.ports))
    for oPort in oInterface.ports:
        oPortProfile = port_profile.PortProfile(oPort, oTraceList, oPart, None)
        lLines.extend(generate_port_constraints(oPortProfile))
    return lLines


def generate_clocks(lPorts):
    lLines = []
    lClockNames = []
    for oPort in lPorts:
        if oPort.capture_clock.name not in lClockNames:
            lClockNames.append(oPort.capture_clock.name)
            lLines.append(create_generated_clock(oPort))
    return lLines


def create_generated_clock(oPort):
    oCaptureClock = oPort.capture_clock
    oGenerator = oCaptureClock.generator
    sSourcePin = format_pin(oGenerator.source, oGenerator.master_pin)
    sTargetPin = format_pin(oGenerator.source, oGenerator.target_pin)
    sRatio = format_ratio(oPort.launch_clock.period, oCaptureClock.period)
    return f'create_generated_clock -name {oCaptureClock.name} -source {sSourcePin} {sRatio} {sTargetPin}'


def format_pin(sCell, sPin):
    return f'[get_pins {sCell}/{sPin}]'


def format_ratio(fLaunchPeriod, fCapturePeriod):
    if fCapturePeriod < fLaunchPeriod:
        return f'-multiply_by {calculate_ratio(fLaunchPeriod, fCapturePeriod)}'
    return f'-divide_by {calculate_ratio(fCapturePeriod, fLaunchPeriod)}'


def calculate_ratio(fLongerPeriod, fShorterPeriod):
    return round(fLongerPeriod / fShorterPeriod)


def generate_port_constraints(oPortProfile):
    lLines = []
    lLines.append(create_max_output_delay(oPortProfile))
    lLines.append(create_min_output_delay(oPortProfile))
    return lLines


def create_max_output_delay(oPortProfile):
    fDelay = output_delays.calculate_expected_max_output_delay(oPortProfile)
    return create_output_delay(oPortProfile.port, '-max', fDelay)


def create_min_output_delay(oPortProfile):
    fDelay = output_delays.calculate_expected_min_output_delay(oPortProfile)
    return create_output_delay(oPortProfile.port, '-min', fDelay)


def create_output_delay(oPort, sLimit, fDelay):
    sClock = format_capture_clock(oPort.capture_clock)
    sReferencePin = f'-reference_pin [get_ports {oPort.capture_clock.port}]'
    return f'set_output_delay {sClock} {sReferencePin} {sLimit} {fDelay:.3f} [get_ports {oPort.name}]'


def format_capture_clock(oCaptureClock):
    sClock = f'-clock [get_clocks {oCaptureClock.name}]'
    if is_falling_edge(oCaptureClock.setup_edge):
        return sClock + ' -clock_fall'
    return sClock


def is_falling_edge(sEdgeLetter):
    return edge_times.convert_edge_letter_to_number(sEdgeLetter) % 2 == 1
