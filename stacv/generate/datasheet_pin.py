'''
Works out the timing of each port at the device's pins, against the edge of the clock the device forwards, from its timing reports.

The values are the worst of every timing report of the port: the worst setup report and the worst hold report.
Every setup report of a port gives the same requirement and port delay, as do its hold reports, so the worst slack gives the worst value.

Each methodology has fixed symbols.  A symbol that more than one port gives is numbered, tSU_1, tSU_2, ..., in the
order of the ports, so each symbol is one value; the symbols of a port share its number.
'''

from stacv.generate import generate_error
from stacv.output import number_format
from stacv.rules import edge_times

RISING = 'Rising'
FALLING = 'Falling'
SUPPORTED_METHODOLOGIES = ['SDR-SS-O', 'SDR-SS-O-FLC', 'SDR-SS-RT-DI']


class DatasheetParameter():
    '''
    One timing value of a pin: the part file key it is written to, its symbol and its value in ns.
    '''

    def __init__(self, sKey, sSymbol, fValue):
        self.key = sKey
        self.base_symbol = sSymbol
        self.symbol = sSymbol
        self.value = fValue


class DatasheetPin():
    '''
    The timing of one port, as a part file pin of the device.
    '''

    def __init__(self, oPort):
        self.port = oPort
        self.clock_port = oPort.forwarded_clock.port
        self.max_frequency = 1000 / oPort.forwarded_clock.period
        # The part file key of the edge the values are against, and that edge.
        self.edge_key = None
        self.edge = None
        # In the order of the datasheet's table; the part file lists them in the order of toml_keys.
        self.parameters = []
        self.toml_keys = []
        # Whether a value is moved from one edge of the clock to the other, which assumes both leave with the same delay.
        self.moves_between_edges = False
        self.section = None

    def get_parameter(self, sKey):
        for oParameter in self.parameters:
            if oParameter.key == sKey:
                return oParameter
        return None


class RoundTripPin(DatasheetPin):
    '''
    The data the part launches, which the device captures a fixed time later with its own clock.
    '''

    def __init__(self, oPort):
        DatasheetPin.__init__(self, oPort)
        self.launch_edge = None
        # From the launch edge: when the device captures, and when the data must be valid until the next data may change.
        self.capture_time = None
        self.valid_from = None
        self.valid_until = None


def is_supported(oPort):
    return oPort.methodology in SUPPORTED_METHODOLOGIES


def build_pin(oPort, oTimingReports):
    oSetupReport = find_worst_report(oTimingReports.get_setup_reports())
    oHoldReport = find_worst_report(oTimingReports.get_hold_reports())
    if oPort.methodology == 'SDR-SS-O':
        return build_output_pin(oPort, oSetupReport, oHoldReport)
    if oPort.methodology == 'SDR-SS-O-FLC':
        return build_first_last_clock_pin(oPort, oSetupReport, oHoldReport)
    return build_round_trip_pin(oPort, oSetupReport, oHoldReport)


def find_worst_report(lTimingReports):
    oWorstReport = None
    for oTimingReport in lTimingReports:
        if oWorstReport is None or oTimingReport.slack < oWorstReport.slack:
            oWorstReport = oTimingReport
    return oWorstReport


def build_output_pin(oPort, oSetupReport, oHoldReport):
    # The clock to out is from the clock edge the data is launched with, so the launch must be on a clock edge.
    # The data changes no later than the setup capture edge less the time it is valid before it,
    # and no earlier than the hold capture edge plus the time it is valid after it.
    oPin = DatasheetPin(oPort)
    oPin.edge_key = 'launch_edge'
    oPin.edge = find_launch_edge(oPort)
    fClockToOutMaximum = oSetupReport.requirement - oSetupReport.slack - oSetupReport.output_delay
    fClockToOutMinimum = oHoldReport.requirement + oHoldReport.slack - oHoldReport.output_delay
    oPin.parameters.append(DatasheetParameter('cko_min', 'tCOmin', fClockToOutMinimum))
    oPin.parameters.append(DatasheetParameter('cko_max', 'tCOmax', fClockToOutMaximum))
    oPin.toml_keys = ['cko_max', 'cko_min']
    oPin.moves_between_edges = oPin.edge != find_capture_edge(oPort)
    return oPin


def build_first_last_clock_pin(oPort, oSetupReport, oHoldReport):
    # Valid before the first capture edge, and after the last.
    oPin = DatasheetPin(oPort)
    oPin.edge_key = 'launch_edge'
    oPin.edge = find_capture_edge(oPort)
    fValidBefore = oSetupReport.slack + oSetupReport.output_delay
    fValidAfter = oHoldReport.slack - oHoldReport.output_delay
    oPin.parameters.append(DatasheetParameter('valid_before', 'tB', fValidBefore))
    oPin.parameters.append(DatasheetParameter('valid_after', 'tA', fValidAfter))
    oPin.toml_keys = ['valid_before', 'valid_after']
    return oPin


def build_round_trip_pin(oPort, oSetupReport, oHoldReport):
    # The setup and hold are to the forwarded clock edge after the launch edge, half a period later:
    # the device captures with its own clock, which the part cannot see.
    # The data launched on an edge must be valid by the maximum input delay plus the setup slack after it.
    # The data the hold check launches must not change before the minimum input delay less the hold slack, which
    # replaces the data launched (setup requirement - hold requirement) before it.
    oPin = RoundTripPin(oPort)
    oPin.launch_edge = find_edge_type(oPort.launch_clock.setup_edge)
    oPin.edge_key = 'capture_edge'
    oPin.edge = find_other_edge(oPin.launch_edge)
    fHalfPeriod = oPort.launch_clock.period / 2
    fEarliestChange = oHoldReport.input_delay - oHoldReport.slack
    oPin.capture_time = oSetupReport.requirement
    oPin.valid_from = oSetupReport.input_delay + oSetupReport.slack
    oPin.valid_until = fEarliestChange + oSetupReport.requirement - oHoldReport.requirement
    oPin.parameters.append(DatasheetParameter('setup', 'tSU', fHalfPeriod - oPin.valid_from))
    oPin.parameters.append(DatasheetParameter('hold', 'tH', oPin.valid_until - fHalfPeriod))
    oPin.toml_keys = ['setup', 'hold']
    oPin.moves_between_edges = True
    return oPin


def find_launch_edge(oPort):
    # The forwarded clock's edge at the time of each launch edge; the setup and hold launches must be on the same kind.
    sSetupEdge = find_forwarded_edge_at_launch(oPort, oPort.launch_clock.setup_edge)
    sHoldEdge = find_forwarded_edge_at_launch(oPort, oPort.launch_clock.hold_edge)
    if sSetupEdge != sHoldEdge:
        raise generate_error.GenerateError('generate_011', oPort.name, f'setup launch edge {oPort.launch_clock.setup_edge} is at a {sSetupEdge.lower()} edge of {oPort.capture_clock.name} and hold launch edge {oPort.launch_clock.hold_edge} at a {sHoldEdge.lower()} edge; the datasheet gives the clock to out from one edge')
    return sSetupEdge


def find_forwarded_edge_at_launch(oPort, iLaunchEdge):
    fLaunchTime = edge_times.calculate_edge_time(oPort.launch_clock.period, iLaunchEdge)
    fHalfPeriod = oPort.capture_clock.period / 2
    fEdges = fLaunchTime / fHalfPeriod
    iEdge = round(fEdges)
    if abs(fEdges - iEdge) > 1e-9:
        raise generate_error.GenerateError('generate_011', oPort.name, f'launch edge {iLaunchEdge} at {format_time(fLaunchTime)} is not at an edge of {oPort.capture_clock.name}; the datasheet gives the clock to out from the clock edge the data is launched with')
    return find_edge_type(iEdge)


def find_capture_edge(oPort):
    return find_edge_type(edge_times.convert_edge_letter_to_number(oPort.capture_clock.setup_edge))


def find_edge_type(iEdgeNumber):
    # Each clock rises at edge 0.
    if iEdgeNumber % 2 == 0:
        return RISING
    return FALLING


def find_other_edge(sEdge):
    if sEdge == RISING:
        return FALLING
    return RISING


def number_repeated_symbols(lPins):
    # A symbol given by more than one port is numbered in the order of the ports.
    dCounts = count_symbols(lPins)
    dNumbers = {}
    for oPin in lPins:
        for oParameter in oPin.parameters:
            if dCounts[oParameter.base_symbol] > 1:
                dNumbers[oParameter.base_symbol] = dNumbers.get(oParameter.base_symbol, 0) + 1
                oParameter.symbol = f'{oParameter.base_symbol}_{dNumbers[oParameter.base_symbol]}'


def count_symbols(lPins):
    dCounts = {}
    for oPin in lPins:
        for oParameter in oPin.parameters:
            dCounts[oParameter.base_symbol] = dCounts.get(oParameter.base_symbol, 0) + 1
    return dCounts


def format_time(fTime):
    return f'{number_format.format_number(fTime)} ns'
