'''
Generates Vivado timing constraints for the ports of an interface.
'''

from stacv.generate import generate_error
from stacv.rules import edge_times
from stacv.rules import output_delays
from stacv.rules import path_lookups
from stacv.rules import requirements
from stacv.rules import tolerance

TOLERANCE = 0.0005


def create_generated_clock(oPort, oInterface):
    check_generator_exists(oPort)
    oCaptureClock = oPort.capture_clock
    oGenerator = oCaptureClock.generator
    sSourcePin = format_pin(oGenerator.source, oGenerator.master_pin)
    sTargetPin = format_pin(oGenerator.source, oGenerator.target_pin)
    oMasterClock = oInterface.get_clock_named(oGenerator.master_clock)
    sRatio = format_ratio(oMasterClock.period, oCaptureClock.period)
    return f'create_generated_clock -name {oCaptureClock.name} -source {sSourcePin} {sRatio} {sTargetPin}'


def check_generator_exists(oPort):
    if oPort.capture_clock.generator is None:
        raise generate_error.GenerateError('generate_001', oPort.name, f'capture clock {oPort.capture_clock.name} has no generator')


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
    if not oPortProfile.traces.trace_starts_with_device_pin_named(oPort.name):
        raise generate_error.GenerateError('generate_007', oPort.name, 'has no trace from the device to the part')
    oDataTrace = path_lookups.get_data_trace(oPortProfile)
    if not oPortProfile.part.has_pin_named(oDataTrace.part_pin):
        raise generate_error.GenerateError('generate_008', oPort.name, f'trace {oDataTrace.name} ends at pin {oDataTrace.part_pin}, which the part does not have')
    oPartPin = path_lookups.get_part_pin_at_end_of_trace(oPortProfile, oDataTrace)
    if path_lookups.get_clock_trace(oPortProfile, oPartPin) is None:
        raise generate_error.GenerateError('generate_009', oPort.name, f'has no clock trace from {oPort.capture_clock.port} to part pin {oPartPin.clock.pin}')


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
    sEdge = select_moved_edge(oPort)
    return f'set_multicycle_path {iMulticycle} {sCheck} {sEdge} -from [get_clocks {oPort.launch_clock.name}] -to [get_ports {oPort.name}]'


def select_moved_edge(oPort):
    if launch_clock_is_faster(oPort):
        return '-start'
    return '-end'


def launch_clock_is_faster(oPort):
    return oPort.launch_clock.period < oPort.capture_clock.period
