'''
Generates Vivado timing constraints for the ports of an interface.
'''


def generate_constraints(oInterface):
    lLines = []
    lLines.extend(generate_clocks(oInterface.ports))
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
