'''
Generates Vivado timing constraints for the ports of an interface.
'''

from stacv.generate import generate_error
from stacv.methodology import methodology
from stacv.rules import input_delays
from stacv.rules import output_delays
from stacv.rules import path_lookups
from stacv.rules import requirements
from stacv.rules import tolerance

TOLERANCE = 0.0005


def create_generated_clock(oPort, oInterface, bAdd):
    check_generator_exists(oPort)
    oForwardedClock = oPort.forwarded_clock
    oGenerator = oForwardedClock.generator
    sSourcePin = format_pin(oGenerator.source, oGenerator.master_pin)
    sTargetPin = format_pin(oGenerator.source, oGenerator.target_pin)
    oMasterClock = oInterface.get_clock_named(oGenerator.master_clock)
    sRatio = format_ratio(oMasterClock.period, oForwardedClock.period)
    return f'create_generated_clock {format_add(bAdd, oGenerator)}-name {oForwardedClock.name} -source {sSourcePin} {sRatio} {sTargetPin}'


def format_add(bAdd, oGenerator):
    # Without -add, a clock generated at a pin that already has one replaces it.
    # Vivado needs the master clock of a clock generated with -add.
    if bAdd:
        return f'-add -master_clock [get_clocks {oGenerator.master_clock}] '
    return ''


def is_generated_at_the_same_pin(oFirstGenerator, oSecondGenerator):
    if oFirstGenerator.source != oSecondGenerator.source:
        return False
    return oFirstGenerator.target_pin == oSecondGenerator.target_pin


def check_generator_exists(oPort):
    if oPort.forwarded_clock.generator is None:
        sClockRole = methodology.describe_clock_key(oPort.forwarded_clock_key)
        raise generate_error.GenerateError('generate_001', oPort.name, f'{sClockRole} {oPort.forwarded_clock.name} has no generator')


def format_pin(sCell, sPin):
    return f'[get_pins {sCell}/{sPin}]'


def format_ratio(fMasterPeriod, fCapturePeriod):
    if fCapturePeriod < fMasterPeriod:
        return f'-multiply_by {calculate_ratio(fMasterPeriod, fCapturePeriod)}'
    return f'-divide_by {calculate_ratio(fCapturePeriod, fMasterPeriod)}'


def calculate_ratio(fLongerPeriod, fShorterPeriod):
    return round(fLongerPeriod / fShorterPeriod)


def check_traces_exist(oPortProfile):
    oPort = oPortProfile.port
    oDataTrace = path_lookups.get_port_data_trace(oPortProfile)
    if oDataTrace is None:
        raise generate_error.GenerateError('generate_007', oPort.name, f'has no trace {describe_data_trace_direction(oPort)}')
    if not oPortProfile.part.has_pin_named(oDataTrace.part_pin, oPort.part_pin_methodology):
        raise generate_error.GenerateError('generate_008', oPort.name, f'trace {oDataTrace.name} {describe_part_end_of_trace(oPort)} pin {oDataTrace.part_pin}, which the part does not have{describe_pin_methodology(oPort)}')
    oPartPin = path_lookups.get_part_pin_at_end_of_trace(oPortProfile, oDataTrace)
    if path_lookups.get_clock_trace(oPortProfile, oPartPin) is None:
        raise generate_error.GenerateError('generate_009', oPort.name, f'has no clock trace {describe_clock_trace(oPort, oPartPin)}')
    if oPort.clock_origin == methodology.SOURCE_CLOCK and path_lookups.get_source_to_part_clock_trace(oPortProfile, oPartPin) is None:
        raise generate_error.GenerateError('generate_009', oPort.name, f'has no clock trace from the source of {oPort.forwarded_clock.port} to part pin {oPartPin.clock.pin}')


def describe_pin_methodology(oPort):
    # The SDR-SS-O pins keep the message they had before pins were looked up by methodology.
    if oPort.part_pin_methodology == 'SDR-SS-I' or oPort.part_pin_methodology == 'SDR-SS-RT-DO':
        return ''
    return f' with methodology {oPort.part_pin_methodology}'


def describe_clock_trace(oPort, oPartPin):
    if oPort.clock_origin == methodology.PART_CLOCK:
        return f'from part pin {oPartPin.clock.pin} to {oPort.forwarded_clock.port}'
    if oPort.clock_origin == methodology.SOURCE_CLOCK:
        return f'from a clock source to {oPort.forwarded_clock.port}'
    return f'from {oPort.forwarded_clock.port} to part pin {oPartPin.clock.pin}'


def format_port(sPortName):
    # A bus, written NAME[upper:lower], is every bit of the port; braces keep Tcl from reading the brackets as a command.
    if '[' in sPortName:
        return '{' + sPortName.split('[')[0] + '[*]}'
    return sPortName


def create_clock(oClock):
    # A clock that comes into the device is defined on the port it enters on.
    return f'create_clock -name {oClock.name} -period {oClock.period:.3f} [get_ports {oClock.port}]'


def is_generated(oPort):
    return oPort.clock_origin == methodology.DEVICE_CLOCK


def is_input(oPort):
    return oPort.data_direction == methodology.INPUT


def describe_part_end_of_trace(oPort):
    if is_input(oPort):
        return 'starts at'
    return 'ends at'


def describe_data_trace_direction(oPort):
    if is_input(oPort):
        return 'from the part to the device'
    return 'from the device to the part'


def create_max_output_delay(oPortProfile):
    fDelay = output_delays.calculate_expected_max_output_delay(oPortProfile)
    return create_output_delay(oPortProfile.port, '-max', fDelay)


def create_min_output_delay(oPortProfile):
    fDelay = output_delays.calculate_expected_min_output_delay(oPortProfile)
    return create_output_delay(oPortProfile.port, '-min', fDelay)


def create_output_delay(oPort, sLimit, fDelay, sEdgeOptions=None):
    return create_port_delay('set_output_delay', oPort, sLimit, fDelay, sEdgeOptions)


def create_port_delay(sCommand, oPort, sLimit, fDelay, sEdgeOptions):
    # A double data rate port gets a second delay for the falling edges, added to the first.
    lWords = [sCommand]
    if sEdgeOptions is None:
        lWords.append(format_forwarded_clock(oPort))
    else:
        lWords.append(f'-clock [get_clocks {oPort.forwarded_clock.name}] {sEdgeOptions}')
    if is_generated(oPort):
        lWords.append(f'-reference_pin [get_ports {oPort.forwarded_clock.port}]')
    lWords.append(f'{sLimit} {fDelay:.3f} [get_ports {format_port(oPort.name)}]')
    return ' '.join(lWords)


def create_max_input_delay(oPortProfile):
    fDelay = input_delays.calculate_expected_max_input_delay(oPortProfile)
    return create_input_delay(oPortProfile.port, '-max', fDelay)


def create_min_input_delay(oPortProfile):
    fDelay = input_delays.calculate_expected_min_input_delay(oPortProfile)
    return create_input_delay(oPortProfile.port, '-min', fDelay)


def create_input_delay(oPort, sLimit, fDelay, sEdgeOptions=None):
    return create_port_delay('set_input_delay', oPort, sLimit, fDelay, sEdgeOptions)


def format_forwarded_clock(oPort):
    # The delays are measured from the forwarded clock's setup edge, so a falling setup edge needs -clock_fall.
    sClock = f'-clock [get_clocks {oPort.forwarded_clock.name}]'
    if forwarded_clock_setup_edge_is_falling(oPort):
        return sClock + ' -clock_fall'
    return sClock


def forwarded_clock_setup_edge_is_falling(oPort):
    if oPort.forwarded_clock_key == methodology.LAUNCH_CLOCK:
        return is_falling_launch_edge(oPort.forwarded_clock.setup_edge)
    return is_falling_edge(oPort.forwarded_clock.setup_edge)


def is_falling_edge(iEdgeNumber):
    return iEdgeNumber % 2 == 1


def is_falling_launch_edge(iEdgeNumber):
    return iEdgeNumber % 2 == 1


def calculate_setup_multicycle(oPort):
    return count_setup_step_periods(oPort)


def calculate_hold_multicycle(oPort):
    return count_setup_step_periods(oPort) - count_hold_step_periods(oPort) - 1


def count_setup_step_periods(oPort):
    fSetupRequirement = requirements.calculate_configuration_setup_requirement(oPort)
    return count_step_periods(oPort, fSetupRequirement, 'generate_002', 'setup requirement')


def count_hold_step_periods(oPort):
    fHoldRequirement = requirements.calculate_configuration_hold_requirement(oPort)
    return count_step_periods(oPort, fHoldRequirement, 'generate_003', 'hold requirement')


def count_step_periods(oPort, fRequirement, sIdentifier, sRequirementName):
    fStepPeriod = find_step_period(oPort)
    iStepPeriods = round(fRequirement / fStepPeriod)
    if not tolerance.is_within_tolerance(iStepPeriods * fStepPeriod, fRequirement, TOLERANCE):
        raise generate_error.GenerateError(sIdentifier, oPort.name, f'{sRequirementName} {fRequirement:.3f}ns is not a whole number of {fStepPeriod:.3f}ns step periods')
    return iStepPeriods


def check_setup_multicycle(oPort, iSetupMulticycle):
    # A setup multicycle of 0 captures the data on the edge that launches it, after the clock's delay to the register.
    if iSetupMulticycle < 0:
        raise generate_error.GenerateError('generate_004', oPort.name, f'setup multicycle {iSetupMulticycle} is less than 0')


def create_edge_multicycle_path(oPort, iMulticycle, sCheck, sLaunchEdge, sCaptureEdge):
    sPort = format_port(oPort.name)
    sEdge = select_moved_edge(oPort)
    return f'set_multicycle_path {iMulticycle} {sCheck} {sEdge} -{sLaunchEdge}_from [get_clocks {oPort.launch_clock.name}] -through [get_ports {sPort}] -{sCaptureEdge}_to [get_clocks {oPort.capture_clock.name}]'


def create_edge_false_path(oPort, sCheck, sLaunchEdge, sCaptureEdge):
    sPort = format_port(oPort.name)
    return f'set_false_path {sCheck} -{sLaunchEdge}_from [get_clocks {oPort.launch_clock.name}] -through [get_ports {sPort}] -{sCaptureEdge}_to [get_clocks {oPort.capture_clock.name}]'


def check_hold_multicycle(oPort, iHoldMulticycle):
    if iHoldMulticycle < 0:
        raise generate_error.GenerateError('generate_005', oPort.name, f'hold multicycle {iHoldMulticycle} is less than 0')


def find_step_period(oPort):
    return min(find_clock_step(oPort, oPort.launch_clock), find_clock_step(oPort, oPort.capture_clock))


def find_clock_step(oPort, oClock):
    # The double data rate clock has an edge every half period.
    if oPort.double_data_rate and oClock.name == oPort.forwarded_clock.name:
        return oClock.period / 2
    return oClock.period


def create_multicycle_path(oPort, iMulticycle, sCheck):
    # The path starts or ends at the port, and the other end is the device clock.
    sEdge = select_moved_edge(oPort)
    if is_input(oPort):
        return f'set_multicycle_path {iMulticycle} {sCheck} {sEdge} -from [get_ports {format_port(oPort.name)}] -to [get_clocks {oPort.capture_clock.name}]'
    return f'set_multicycle_path {iMulticycle} {sCheck} {sEdge} -from [get_clocks {oPort.launch_clock.name}] -to [get_ports {format_port(oPort.name)}]'


def select_moved_edge(oPort):
    if launch_clock_is_faster(oPort):
        return '-start'
    return '-end'


def launch_clock_is_faster(oPort):
    return find_clock_step(oPort, oPort.launch_clock) < find_clock_step(oPort, oPort.capture_clock)
