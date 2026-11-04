'''
Calculates the output or input delays of the methodologies whose clock comes from the part or from a clock source,
and of double data rate, with the calculation each value comes from.

Each delay is the time from the clock edge at the device's clock port to the data at the data port:
    clock from the part:    the clock reaches the device after its trace, and the data after the part's clock to out and its trace.
    clock from a source:    the clock reaches the device and the part on their own traces, so the difference between them moves the part's edge.
'''

from stacv.output import number_format
from stacv.rules import part_timing
from stacv.rules import path_lookups


class Delay():

    def __init__(self, fValue, lLines):
        self.value = fValue
        self.lines = lLines


class Inputs():
    '''
    The traces and part pin values one delay calculation reads.
    '''

    def __init__(self, oPortProfile):
        oPort = oPortProfile.port
        oDataTrace = path_lookups.get_port_data_trace(oPortProfile)
        self.port = oPort
        self.data_trace_name = oDataTrace.name
        self.data = path_lookups.get_data_trace_delay(oPortProfile, oDataTrace)
        self.pin = path_lookups.get_part_pin_at_end_of_trace(oPortProfile, oDataTrace)
        oClockTrace = path_lookups.get_clock_trace(oPortProfile, self.pin)
        self.clock_trace_name = oClockTrace.name
        self.clock = path_lookups.get_clock_trace_delay(oPortProfile, oClockTrace)
        oPartClockTrace = path_lookups.get_source_to_part_clock_trace(oPortProfile, self.pin)
        if oPartClockTrace is not None:
            self.part_clock_trace_name = oPartClockTrace.name
            self.part_clock = oPartClockTrace.source_to_part


def calculate_delays(oPortProfile):
    # Returns the maximum and minimum delay of the port.
    oInputs = Inputs(oPortProfile)
    sMethodology = oPortProfile.port.methodology
    if sMethodology in ['SDR-SS-I', 'DDR-SS-I-SE', 'DDR-SS-I-NE']:
        return calculate_input_from_part_clock(oInputs)
    if sMethodology == 'SDR-SS-RT-DO':
        return calculate_output_on_part_clock(oInputs)
    if sMethodology == 'SDR-SYS-O':
        return calculate_system_synchronous_output(oInputs)
    if sMethodology == 'SDR-SYS-I':
        return calculate_system_synchronous_input(oInputs)
    return calculate_output_on_device_clock(oInputs)


def calculate_input_from_part_clock(oInputs):
    # The part's clock and data both travel to the device, so the clock trace is subtracted.
    oCkoMax = part_timing.get_clock_to_out_max(oInputs.pin, oInputs.port)
    oCkoMin = part_timing.get_clock_to_out_min(oInputs.pin, oInputs.port)
    oMax = build_delay(oCkoMax.calculation, [(oCkoMax.name, oCkoMax.value), ('+', f'{oInputs.data_trace_name} maximum', oInputs.data.max_delay), ('-', f'{oInputs.clock_trace_name} minimum', oInputs.clock.min_delay)])
    oMin = build_delay(oCkoMin.calculation, [(oCkoMin.name, oCkoMin.value), ('+', f'{oInputs.data_trace_name} minimum', oInputs.data.min_delay), ('-', f'{oInputs.clock_trace_name} maximum', oInputs.clock.max_delay)])
    return oMax, oMin


def calculate_output_on_part_clock(oInputs):
    # The part's clock reaches the part before it reaches the device, so the clock trace is added.
    oSetup = part_timing.get_setup(oInputs.pin, oInputs.port)
    oHold = part_timing.get_hold(oInputs.pin, oInputs.port)
    oMax = build_delay(oSetup.calculation, [(f'{oInputs.data_trace_name} maximum', oInputs.data.max_delay), ('+', oSetup.name, oSetup.value), ('+', f'{oInputs.clock_trace_name} maximum', oInputs.clock.max_delay)])
    oMin = build_delay(oHold.calculation, [(f'{oInputs.data_trace_name} minimum', oInputs.data.min_delay), ('-', oHold.name, oHold.value), ('+', f'{oInputs.clock_trace_name} minimum', oInputs.clock.min_delay)])
    return oMax, oMin


def calculate_system_synchronous_output(oInputs):
    # The part's clock edge comes the difference of the two clock traces after the device's.
    oSetup = part_timing.get_setup(oInputs.pin, oInputs.port)
    oHold = part_timing.get_hold(oInputs.pin, oInputs.port)
    oMax = build_delay(oSetup.calculation, [(f'{oInputs.data_trace_name} maximum', oInputs.data.max_delay), ('+', oSetup.name, oSetup.value), ('-', f'{oInputs.part_clock_trace_name} minimum', oInputs.part_clock.min_delay), ('+', f'{oInputs.clock_trace_name} maximum', oInputs.clock.max_delay)])
    oMin = build_delay(oHold.calculation, [(f'{oInputs.data_trace_name} minimum', oInputs.data.min_delay), ('-', oHold.name, oHold.value), ('-', f'{oInputs.part_clock_trace_name} maximum', oInputs.part_clock.max_delay), ('+', f'{oInputs.clock_trace_name} minimum', oInputs.clock.min_delay)])
    return oMax, oMin


def calculate_system_synchronous_input(oInputs):
    oCkoMax = part_timing.get_clock_to_out_max(oInputs.pin, oInputs.port)
    oCkoMin = part_timing.get_clock_to_out_min(oInputs.pin, oInputs.port)
    oMax = build_delay(oCkoMax.calculation, [(f'{oInputs.part_clock_trace_name} maximum', oInputs.part_clock.max_delay), ('-', f'{oInputs.clock_trace_name} minimum', oInputs.clock.min_delay), ('+', oCkoMax.name, oCkoMax.value), ('+', f'{oInputs.data_trace_name} maximum', oInputs.data.max_delay)])
    oMin = build_delay(oCkoMin.calculation, [(f'{oInputs.part_clock_trace_name} minimum', oInputs.part_clock.min_delay), ('-', f'{oInputs.clock_trace_name} maximum', oInputs.clock.max_delay), ('+', oCkoMin.name, oCkoMin.value), ('+', f'{oInputs.data_trace_name} minimum', oInputs.data.min_delay)])
    return oMax, oMin


def calculate_output_on_device_clock(oInputs):
    # The same calculation as SDR-SS-O, with the part's setup and hold in either form.
    oSetup = part_timing.get_setup(oInputs.pin, oInputs.port)
    oHold = part_timing.get_hold(oInputs.pin, oInputs.port)
    oMax = build_delay(oSetup.calculation, [(f'{oInputs.data_trace_name} maximum', oInputs.data.max_delay), ('-', f'{oInputs.clock_trace_name} minimum', oInputs.clock.min_delay), ('+', oSetup.name, oSetup.value)])
    oMin = build_delay(oHold.calculation, [(f'{oInputs.data_trace_name} minimum', oInputs.data.min_delay), ('-', f'{oInputs.clock_trace_name} maximum', oInputs.clock.max_delay), ('-', oHold.name, oHold.value)])
    return oMax, oMin


def build_delay(lConversions, lTerms):
    # The first term has no sign; each other term is (sign, name, value).
    fValue = lTerms[0][1]
    lNames = [lTerms[0][0]]
    lValues = [format_value(lTerms[0][1])]
    for sSign, sName, fTerm in lTerms[1:]:
        if sSign == '+':
            fValue += fTerm
        else:
            fValue -= fTerm
        lNames.append(f'{sSign} {sName}')
        lValues.append(f'{sSign} {format_value(fTerm)}')
    lLines = []
    lLines.extend(lConversions)
    lLines.append(' '.join(lNames))
    lLines.append(' '.join(lValues))
    lLines.append(f'{format_value(fValue)} ns')
    return Delay(fValue, lLines)


def format_value(fValue):
    return number_format.format_number(fValue)
