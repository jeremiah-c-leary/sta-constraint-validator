'''
Generates Vivado timing constraints for the ports of an interface.
'''

from stacv.generate import generate_error
from stacv.methodology import methodology
from stacv.methodology import methodology_factory
from stacv.rules import edge_times
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
    oDataTrace = find_data_trace(oPortProfile)
    if oDataTrace is None:
        raise generate_error.GenerateError('generate_007', oPort.name, f'has no trace {describe_data_trace_direction(oPort)}')
    if not oPortProfile.part.has_pin_named(oDataTrace.part_pin):
        raise generate_error.GenerateError('generate_008', oPort.name, f'trace {oDataTrace.name} {describe_part_end_of_trace(oPort)} pin {oDataTrace.part_pin}, which the part does not have')
    oPartPin = path_lookups.get_part_pin_at_end_of_trace(oPortProfile, oDataTrace)
    if path_lookups.get_clock_trace(oPortProfile, oPartPin) is None:
        raise generate_error.GenerateError('generate_009', oPort.name, f'has no clock trace from {oPort.forwarded_clock.port} to part pin {oPartPin.clock.pin}')


def is_input(oPort):
    return methodology_factory.create_methodology(oPort.methodology).data_direction == methodology.INPUT


def find_data_trace(oPortProfile):
    if is_input(oPortProfile.port):
        return path_lookups.get_input_data_trace(oPortProfile)
    return path_lookups.get_data_trace(oPortProfile)


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


def create_output_delay(oPort, sLimit, fDelay):
    sClock = format_forwarded_clock(oPort)
    sReferencePin = f'-reference_pin [get_ports {oPort.forwarded_clock.port}]'
    return f'set_output_delay {sClock} {sReferencePin} {sLimit} {fDelay:.3f} [get_ports {oPort.name}]'


def create_max_input_delay(oPortProfile):
    fDelay = input_delays.calculate_expected_max_input_delay(oPortProfile)
    return create_input_delay(oPortProfile.port, '-max', fDelay)


def create_min_input_delay(oPortProfile):
    fDelay = input_delays.calculate_expected_min_input_delay(oPortProfile)
    return create_input_delay(oPortProfile.port, '-min', fDelay)


def create_input_delay(oPort, sLimit, fDelay):
    sClock = format_forwarded_clock(oPort)
    sReferencePin = f'-reference_pin [get_ports {oPort.forwarded_clock.port}]'
    return f'set_input_delay {sClock} {sReferencePin} {sLimit} {fDelay:.3f} [get_ports {oPort.name}]'


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


def is_falling_edge(sEdgeLetter):
    return edge_times.convert_edge_letter_to_number(sEdgeLetter) % 2 == 1


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
    if iSetupMulticycle < 1:
        raise generate_error.GenerateError('generate_004', oPort.name, f'setup multicycle {iSetupMulticycle} is less than 1')


def check_hold_multicycle(oPort, iHoldMulticycle):
    if iHoldMulticycle < 0:
        raise generate_error.GenerateError('generate_005', oPort.name, f'hold multicycle {iHoldMulticycle} is less than 0')


def find_step_period(oPort):
    return min(oPort.launch_clock.period, oPort.capture_clock.period)


def create_multicycle_path(oPort, iMulticycle, sCheck):
    # The path starts or ends at the port, and the other end is the device clock.
    sEdge = select_moved_edge(oPort)
    if is_input(oPort):
        return f'set_multicycle_path {iMulticycle} {sCheck} {sEdge} -from [get_ports {oPort.name}] -to [get_clocks {oPort.capture_clock.name}]'
    return f'set_multicycle_path {iMulticycle} {sCheck} {sEdge} -from [get_clocks {oPort.launch_clock.name}] -to [get_ports {oPort.name}]'


def select_moved_edge(oPort):
    if launch_clock_is_faster(oPort):
        return '-start'
    return '-end'


def launch_clock_is_faster(oPort):
    return oPort.launch_clock.period < oPort.capture_clock.period
